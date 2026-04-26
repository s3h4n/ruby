"""CLI interface for Ruby assistant."""

from __future__ import annotations

import json
import os
import queue
import re
import select
import sys
import threading
import time
import wave
import warnings
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

# Suppress non-actionable warnings from dependencies
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*HF Hub.*")
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

from ruby.app import AppContext, PROJECT_ROOT, build_app_context, dump_settings_snapshot
from ruby.config.settings import DEFAULT_CONFIG_PATH, get_env_status, load_settings
from ruby.core.errors import RubyError, StartupCheckError
from ruby.core.markdown_speech import markdown_to_speech_text
from ruby.core.voice_pipeline import PlaybackQueue, SpeechChunker, TTSSynthesisQueue
from ruby.setup.doctor import run_doctor
from ruby.setup.init_wizard import InitWizard
from ruby.setup.model_discovery import discover_ollama_models, discover_whisper_models


AVAILABLE_COMMANDS = ("run", "init", "doctor", "models", "config")


STATE_READY = "[Ready]"
STATE_LISTENING = "[Listening]"
STATE_TRANSCRIBING = "[Transcribing]"
STATE_THINKING = "[Thinking]"
STATE_SPEAKING = "[Speaking]"
STATE_DONE = "[Done]"
STATE_INTERRUPTED = "[Interrupted]"

ControlPollFn = Callable[[float], str | None]
_WORD_TOKEN = re.compile(r"\b[\w']+\b")


def _print_state(label: str, message: str = "") -> None:
    if message:
        print(f"{label} {message}")
        return
    print(label)


def _print_debug(context: AppContext, label: str, details: str) -> None:
    if not context.settings.debug:
        return
    print(f"[Debug] {label}: {details}")


def _latency_logging_enabled(context: AppContext) -> bool:
    return bool(context.settings.debug and context.settings.audio.latency_debug)


def _print_latency(context: AppContext, label: str, elapsed_ms: float) -> None:
    if not _latency_logging_enabled(context):
        return
    print(f"[Latency] {label}: {elapsed_ms:.1f}ms")


def _normalize_for_speech(text: str) -> str:
    normalized = markdown_to_speech_text(text)
    return re.sub(r"\s+", " ", normalized).strip()


def _compute_unseen_residual_text(final_text: str, emitted_captions: list[str]) -> str:
    final_speech = _normalize_for_speech(final_text)
    if not final_speech:
        return ""

    emitted_speech = _normalize_for_speech(" ".join(emitted_captions))
    if not emitted_speech:
        return final_speech
    if final_speech in emitted_speech:
        return ""
    if final_speech.startswith(emitted_speech):
        return final_speech[len(emitted_speech) :].strip()

    final_tokens = [token.group(0).lower() for token in _WORD_TOKEN.finditer(final_speech)]
    emitted_tokens = [token.group(0).lower() for token in _WORD_TOKEN.finditer(emitted_speech)]
    if not final_tokens:
        return ""

    overlap = 0
    max_overlap = min(len(final_tokens), len(emitted_tokens))
    for candidate in range(1, max_overlap + 1):
        if emitted_tokens[-candidate:] == final_tokens[:candidate]:
            overlap = candidate

    if overlap >= len(final_tokens):
        return ""
    if overlap > 0:
        return " ".join(final_tokens[overlap:])
    return final_speech


def _estimate_audio_duration_seconds(audio_path: Path, fallback_text: str) -> float:
    try:
        with wave.open(str(audio_path), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
            if frame_rate > 0 and frame_count > 0:
                return max(frame_count / float(frame_rate), 0.08)
    except Exception:  # noqa: BLE001
        pass

    normalized = _normalize_for_speech(fallback_text)
    chars = max(len(normalized), 1)
    return min(max(chars / 24.0, 0.15), 4.0)


def _confirm_action(prompt: str) -> bool:
    choice = input(f"{prompt} [y/N]: ").strip().lower()
    return choice in {"y", "yes"}


def _print_help_commands() -> None:
    print("Available runtime commands:")
    print("  /help     Show command help")
    print("  /history  Show retained conversation turns")
    print("  /clear    Clear in-session conversation history")
    print("  /status   Show active providers and models")
    print("  /quit     Exit the session")
    print("  Ctrl+C or Esc while processing to cancel current turn")


def _print_status(context: AppContext) -> None:
    settings = context.settings
    print("[Status]")
    print(
        f"- STT: {settings.providers.stt.provider} "
        f"(model: {settings.providers.stt.model})"
    )
    print(
        f"- LLM: {settings.providers.llm.provider} "
        f"(model: {settings.providers.llm.model})"
    )
    print(
        f"- TTS: {settings.providers.tts.provider} "
        f"(voice: {settings.providers.tts.voice})"
    )
    conversation_status = "enabled" if settings.conversation.enabled else "disabled"
    print(
        f"- Conversation: {conversation_status} "
        f"(max_turns: {settings.conversation.max_turns})"
    )
    print(f"- Debug: {settings.debug}")
    if settings.debug:
        print(f"- LLM URL: {settings.providers.llm.url}")
        print(f"- whisper-cli: {settings.providers.stt.whisper_cli}")


def _print_history(context: AppContext) -> None:
    history = context.assistant.get_conversation_history()
    if not history:
        print("[History] No retained conversation turns.")
        return

    print("[History]")
    for message in history:
        speaker = "You" if message.get("role") == "user" else "Ruby"
        content = message.get("content", "").strip()
        if content:
            print(f"{speaker}: {content}")


def _handle_runtime_command(context: AppContext, text: str) -> bool:
    normalized = text.strip().lower()
    if normalized == "/help":
        _print_help_commands()
        return False
    if normalized == "/status":
        _print_status(context)
        return False
    if normalized == "/history":
        _print_history(context)
        return False
    if normalized == "/clear":
        context.assistant.clear_conversation()
        print("[Done] Conversation history cleared.")
        return False
    if normalized == "/quit":
        print("[Done] Exiting Ruby session.")
        return True

    print(f"[Error] Unknown command: {text.strip()}")
    print("Use /help to view available commands.")
    return False


def _print_llm_error(context: AppContext, exc: RubyError) -> None:
    message = str(exc)
    lowered = message.lower()
    if context.settings.providers.llm.provider == "ollama" and (
        "could not reach ollama" in lowered
        or "connection refused" in lowered
        or "timed out" in lowered
    ):
        print("[Error] Ollama is not reachable. Start it with: ollama serve")
        _print_debug(context, "llm", message)
        return

    print("[Error] Could not generate a response.")
    _print_debug(context, "llm", message)


def _default_control_poll(timeout_seconds: float) -> str | None:
    if not sys.stdin.isatty():
        if timeout_seconds > 0:
            time.sleep(timeout_seconds)
        return None

    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
    except (OSError, ValueError):
        if timeout_seconds > 0:
            time.sleep(timeout_seconds)
        return None

    if not ready:
        return None

    char = sys.stdin.read(1)
    if char in {"\x03", "\x1b"}:
        return "cancel"
    if char in {"\n", "\r"}:
        return "stop"
    return None


def _run_stage_with_controls(
    run_stage: Callable[[], Any],
    *,
    cancel_event: threading.Event,
    control_poll_fn: ControlPollFn,
    stop_event: threading.Event | None = None,
    poll_seconds: float = 0.05,
) -> tuple[Any | None, bool]:
    result_holder: dict[str, Any] = {}
    error_holder: dict[str, BaseException] = {}

    def _target() -> None:
        try:
            result_holder["value"] = run_stage()
        except BaseException as exc:  # noqa: BLE001
            error_holder["error"] = exc

    worker = threading.Thread(target=_target, daemon=True)
    worker.start()

    while worker.is_alive():
        try:
            signal = control_poll_fn(poll_seconds)
        except KeyboardInterrupt:
            cancel_event.set()
            break
        if signal == "cancel":
            cancel_event.set()
            break
        if signal == "stop" and stop_event is not None:
            stop_event.set()
        if cancel_event.is_set():
            break

    if cancel_event.is_set():
        worker.join(timeout=0.05)
        return None, True

    worker.join()
    if "error" in error_holder:
        raise error_holder["error"]
    return result_holder.get("value"), False


def _run_text_request(
    context: AppContext,
    user_text: str,
    *,
    cancel_event: threading.Event | None = None,
    control_poll_fn: ControlPollFn | None = None,
) -> bool:
    cleaned = user_text.strip()
    if not cleaned:
        return False

    cancel_event = cancel_event or threading.Event()
    control_poll = control_poll_fn or _default_control_poll

    print(f"You said: {cleaned}")
    _print_state(STATE_THINKING)

    def _generate_response() -> Any:
        return context.assistant.handle_text(cleaned)

    try:
        response, interrupted = _run_stage_with_controls(
            _generate_response,
            cancel_event=cancel_event,
            control_poll_fn=control_poll,
        )
    except RubyError as exc:
        _print_llm_error(context, exc)
        return False

    if interrupted or cancel_event.is_set() or response is None:
        _print_state(STATE_INTERRUPTED)
        _print_state(STATE_READY)
        return True

    print(f"Ruby: {response.text}")
    if response.warning:
        print(f"[Warning] {response.warning}")

    if response.audio_path:
        _print_state(STATE_SPEAKING)

        def _play_audio() -> None:
            audio_path = Path(response.audio_path)
            play_with_cancellation = getattr(context.player, "play_with_cancellation", None)
            if callable(play_with_cancellation):
                play_with_cancellation(audio_path, cancel_event=cancel_event)
                return
            context.player.play(audio_path)

        try:
            _, interrupted = _run_stage_with_controls(
                _play_audio,
                cancel_event=cancel_event,
                control_poll_fn=control_poll,
            )
        except RubyError as exc:
            print("[Warning] Text response generated, but speech failed.")
            _print_debug(context, "playback", str(exc))
            return False

        if interrupted or cancel_event.is_set():
            _print_state(STATE_INTERRUPTED)
            _print_state(STATE_READY)
            return True

    _print_state(STATE_DONE)
    return False


def _run_voice_request(
    context: AppContext,
    *,
    control_poll_fn: ControlPollFn | None = None,
) -> bool:
    control_poll = control_poll_fn or _default_control_poll
    cancel_event = threading.Event()
    stop_recording_event = threading.Event()

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    command_path = PROJECT_ROOT / "recordings" / f"command-{timestamp}.wav"

    _print_state(STATE_LISTENING)

    def _record_audio() -> Any:
        return context.recorder.record(
            context.settings.audio.record_seconds,
            command_path,
            stop_event=stop_recording_event,
            cancel_event=cancel_event,
        )

    try:
        recorded_path, interrupted = _run_stage_with_controls(
            _record_audio,
            cancel_event=cancel_event,
            control_poll_fn=control_poll,
            stop_event=stop_recording_event,
        )
    except Exception as exc:  # noqa: BLE001
        print("[Error] Microphone access failed. Check macOS privacy settings.")
        _print_debug(context, "microphone", str(exc))
        return False

    if interrupted or cancel_event.is_set() or recorded_path is None:
        try:
            command_path.unlink(missing_ok=True)
        except OSError:
            pass
        _print_state(STATE_INTERRUPTED)
        _print_state(STATE_READY)
        return True

    speech_ended_at = time.monotonic()
    _print_state(STATE_TRANSCRIBING)

    def _transcribe() -> Any:
        return context.assistant.stt_provider.transcribe(command_path)

    try:
        transcript, interrupted = _run_stage_with_controls(
            _transcribe,
            cancel_event=cancel_event,
            control_poll_fn=control_poll,
        )
    except RubyError as exc:
        print("[Error] Could not transcribe audio.")
        _print_debug(context, "transcription", str(exc))
        return False

    transcript_ready_at = time.monotonic()
    _print_latency(
        context,
        "speech_end_to_transcript",
        (transcript_ready_at - speech_ended_at) * 1000.0,
    )

    if interrupted or cancel_event.is_set() or not transcript:
        _print_state(STATE_INTERRUPTED)
        _print_state(STATE_READY)
        return True

    print(f"You said: {transcript}")
    _print_state(STATE_THINKING)

    first_token_at: float | None = None
    first_chunk_at: float | None = None
    first_tts_audio_at: float | None = None
    playback_started_at: float | None = None
    playback_stopped_at: float | None = None
    stream_completed_at: float | None = None
    barge_in_detected_at: float | None = None
    barge_in_guard_seconds = 0.02
    barge_in_guard_until = 0.0
    emitted_captions: list[str] = []
    acknowledgement_chunk: str | None = None
    acknowledgement_chunk_handled = False
    response_chunk_seen = False
    caption_thread: threading.Thread | None = None
    caption_stop_event = threading.Event()
    caption_flush_event = threading.Event()
    caption_lock = threading.Lock()

    monitor_stop_event = threading.Event()
    monitor_thread: threading.Thread | None = None
    control_monitor_stop_event = threading.Event()
    control_monitor_thread: threading.Thread | None = None

    def _stop_barge_in_monitor() -> None:
        nonlocal monitor_thread
        monitor_stop_event.set()
        if monitor_thread is not None:
            monitor_thread.join(timeout=0.2)
            monitor_thread = None

    def _stop_control_monitor() -> None:
        nonlocal control_monitor_thread
        control_monitor_stop_event.set()
        if control_monitor_thread is not None:
            control_monitor_thread.join(timeout=0.2)
            control_monitor_thread = None

    def _stop_caption_renderer(*, flush: bool) -> None:
        nonlocal caption_thread
        if caption_thread is None:
            return
        if flush:
            caption_flush_event.set()
        else:
            caption_stop_event.set()
        caption_thread.join(timeout=0.5)
        caption_thread = None

    def _start_caption_renderer(caption: str, audio_path: Path) -> None:
        nonlocal caption_thread

        _stop_caption_renderer(flush=True)

        if not caption:
            return

        if not sys.stdout.isatty():
            print(f"Ruby: {caption}")
            emitted_captions.append(caption)
            return

        caption_stop_event.clear()
        caption_flush_event.clear()
        duration_seconds = _estimate_audio_duration_seconds(audio_path, caption)

        def _render() -> None:
            interval = min(max(duration_seconds / max(len(caption), 1), 0.008), 0.08)
            index = 0
            with caption_lock:
                print("Ruby: ", end="", flush=True)

            while index < len(caption):
                if cancel_event.is_set() or caption_stop_event.is_set():
                    break
                if caption_flush_event.is_set():
                    remainder = caption[index:]
                    if remainder:
                        with caption_lock:
                            print(remainder, end="", flush=True)
                    index = len(caption)
                    break
                with caption_lock:
                    print(caption[index], end="", flush=True)
                index += 1
                time.sleep(interval)

            with caption_lock:
                print()
            if index >= len(caption):
                emitted_captions.append(caption)

        caption_thread = threading.Thread(target=_render, daemon=True)
        caption_thread.start()

    def _start_control_monitor() -> None:
        nonlocal control_monitor_thread

        if control_monitor_thread is not None and control_monitor_thread.is_alive():
            return

        control_monitor_stop_event.clear()

        def _monitor_controls() -> None:
            while not cancel_event.is_set() and not control_monitor_stop_event.is_set():
                try:
                    signal = control_poll(0.05)
                except KeyboardInterrupt:
                    cancel_event.set()
                    return

                if signal == "cancel":
                    cancel_event.set()
                    return

        control_monitor_thread = threading.Thread(target=_monitor_controls, daemon=True)
        control_monitor_thread.start()

    def _start_barge_in_monitor() -> None:
        nonlocal monitor_thread, monitor_stop_event, barge_in_detected_at, barge_in_guard_until

        if not context.settings.audio.barge_in_enabled:
            return

        wait_for_speech = getattr(context.recorder, "wait_for_speech", None)
        if not callable(wait_for_speech):
            return

        _stop_barge_in_monitor()
        monitor_stop_event = threading.Event()
        barge_in_guard_until = max(barge_in_guard_until, time.monotonic() + barge_in_guard_seconds)

        def _monitor() -> None:
            nonlocal barge_in_detected_at
            try:
                detected = wait_for_speech(
                    cancel_event=cancel_event,
                    stop_event=monitor_stop_event,
                    energy_threshold=context.settings.audio.barge_in_energy_threshold,
                )
            except Exception as exc:  # noqa: BLE001
                _print_debug(context, "barge_in", str(exc))
                return
            detection_time = time.monotonic()
            if (
                detected
                and not cancel_event.is_set()
                and not monitor_stop_event.is_set()
                and detection_time >= barge_in_guard_until
            ):
                barge_in_detected_at = time.monotonic()
                cancel_event.set()

        monitor_thread = threading.Thread(target=_monitor, daemon=True)
        monitor_thread.start()

    def _on_first_token(_latency_ms: float) -> None:
        nonlocal first_token_at
        if first_token_at is None:
            first_token_at = time.monotonic()

    def _on_first_audio_ready() -> None:
        nonlocal first_tts_audio_at
        if first_tts_audio_at is None:
            first_tts_audio_at = time.monotonic()

    def _on_playback_start() -> None:
        nonlocal playback_started_at
        if playback_started_at is None:
            playback_started_at = time.monotonic()
            _print_state(STATE_SPEAKING)

    def _on_playback_stop() -> None:
        nonlocal playback_stopped_at
        playback_stopped_at = time.monotonic()

    def _on_chunk_start(text: str, audio_path: Path) -> None:
        nonlocal acknowledgement_chunk_handled, response_chunk_seen
        caption = text.strip()
        _start_caption_renderer(caption, audio_path)

        if (
            acknowledgement_chunk is not None
            and not acknowledgement_chunk_handled
            and caption == acknowledgement_chunk
        ):
            acknowledgement_chunk_handled = True
            return

        if not response_chunk_seen:
            response_chunk_seen = True
            return

        _start_barge_in_monitor()

    def _on_chunk_end() -> None:
        nonlocal barge_in_guard_until
        _stop_caption_renderer(flush=True)
        barge_in_guard_until = max(barge_in_guard_until, time.monotonic() + barge_in_guard_seconds)
        _stop_barge_in_monitor()

    chunker = SpeechChunker(
        min_chunk_words=context.settings.audio.min_chunk_words,
        max_chunk_words=context.settings.audio.max_chunk_words,
        max_chunk_wait_ms=context.settings.audio.max_chunk_wait_ms,
    )
    tts_queue = TTSSynthesisQueue(
        tts_provider=context.assistant.tts_provider,
        responses_dir=PROJECT_ROOT / "responses",
        cancel_event=cancel_event,
        on_first_audio_ready=_on_first_audio_ready,
    )
    playback_queue = PlaybackQueue(
        player=context.player,
        source_queue=tts_queue.output_queue,
        cancel_event=cancel_event,
        on_playback_start=_on_playback_start,
        on_playback_stop=_on_playback_stop,
        on_chunk_start=_on_chunk_start,
        on_chunk_end=_on_chunk_end,
    )

    tts_queue.start()
    playback_queue.start()

    if context.assistant.should_acknowledge_for_voice(transcript):
        acknowledgement = context.assistant.acknowledgement_for_voice(transcript)
        acknowledgement_chunk = acknowledgement.strip() or None
        tts_queue.enqueue(acknowledgement)

    full_parts: list[str] = []
    stream_queue: queue.Queue[str | RubyError | None] = queue.Queue()

    def _produce_stream() -> None:
        try:
            for fragment in context.assistant.stream_voice_response(
                transcript,
                cancel_event=cancel_event,
                on_first_token=_on_first_token,
            ):
                if cancel_event.is_set():
                    break
                stream_queue.put(fragment)
        except RubyError as exc:
            stream_queue.put(exc)
        finally:
            stream_queue.put(None)

    stream_thread = threading.Thread(target=_produce_stream, daemon=True)
    stream_thread.start()
    _start_control_monitor()

    stream_finished = False
    try:
        while not stream_finished and not cancel_event.is_set():
            try:
                item = stream_queue.get(timeout=0.05)
            except queue.Empty:
                for chunk in chunker.drain_on_timeout(now_monotonic=time.monotonic()):
                    if first_chunk_at is None:
                        first_chunk_at = time.monotonic()
                    tts_queue.enqueue(chunk)
                continue

            if item is None:
                stream_completed_at = time.monotonic()
                stream_finished = True
                break

            if isinstance(item, RubyError):
                _print_llm_error(context, item)
                cancel_event.set()
                break

            full_parts.append(item)
            for chunk in chunker.feed(item):
                if first_chunk_at is None:
                    first_chunk_at = time.monotonic()
                tts_queue.enqueue(chunk)

        if not cancel_event.is_set():
            for chunk in chunker.drain_on_timeout(now_monotonic=time.monotonic()):
                if first_chunk_at is None:
                    first_chunk_at = time.monotonic()
                tts_queue.enqueue(chunk)
            for chunk in chunker.flush():
                if first_chunk_at is None:
                    first_chunk_at = time.monotonic()
                tts_queue.enqueue(chunk)
    finally:
        _stop_control_monitor()
        _stop_caption_renderer(flush=False)
        stream_thread.join(timeout=0.2)
        tts_queue.close()
        tts_queue.join()
        playback_queue.join()
        _stop_barge_in_monitor()

    final_text = "".join(full_parts).strip()
    interrupted_final = cancel_event.is_set()
    response = context.assistant.finalize_voice_turn(
        transcript,
        final_text,
        interrupted=interrupted_final,
    )

    if response.text and not interrupted_final:
        if not emitted_captions:
            print(f"Ruby: {response.text}")
        else:
            residual_text = _compute_unseen_residual_text(response.text, emitted_captions)
            if residual_text:
                print(f"Ruby: {residual_text}")

    if first_token_at is not None:
        _print_latency(
            context,
            "transcript_to_first_token",
            (first_token_at - transcript_ready_at) * 1000.0,
        )
    if first_token_at is not None and first_chunk_at is not None:
        _print_latency(
            context,
            "first_token_to_first_chunk",
            (first_chunk_at - first_token_at) * 1000.0,
        )
    if first_chunk_at is not None and first_tts_audio_at is not None:
        _print_latency(
            context,
            "first_chunk_to_first_tts_audio",
            (first_tts_audio_at - first_chunk_at) * 1000.0,
        )
    if first_tts_audio_at is not None and playback_started_at is not None:
        _print_latency(
            context,
            "first_tts_audio_to_playback_start",
            (playback_started_at - first_tts_audio_at) * 1000.0,
        )
    if playback_started_at is not None and stream_completed_at is not None:
        _print_latency(
            context,
            "playback_start_to_stream_complete",
            (stream_completed_at - playback_started_at) * 1000.0,
        )
        _print_debug(
            context,
            "overlap",
            (
                "playback_started_before_stream_complete="
                f"{str(playback_started_at < stream_completed_at).lower()}"
            ),
        )
    if barge_in_detected_at is not None and playback_stopped_at is not None:
        _print_latency(
            context,
            "barge_in_to_audio_stop",
            (playback_stopped_at - barge_in_detected_at) * 1000.0,
        )

    if interrupted_final:
        _print_state(STATE_INTERRUPTED)
        _print_state(STATE_READY)
        return True

    _print_state(STATE_DONE)
    return False


def _interactive_loop(context: AppContext) -> int:
    print(f"{context.settings.assistant.name} interactive session started.")

    while True:
        _print_state(
            STATE_READY,
            "Press Enter to record, type a message, or use /help.",
        )
        try:
            user_text = input("Ruby > ")
        except EOFError:
            print("[Done] Exiting Ruby session.")
            return 0
        stripped = user_text.strip()

        if stripped.startswith("/"):
            should_exit = _handle_runtime_command(context, stripped)
            if should_exit:
                return 0
            continue

        if not stripped:
            _run_voice_request(context)
            continue

        _run_text_request(context, stripped)


def run_command(_args: list[str] | None = None) -> int:
    try:
        context = build_app_context(confirm_callback=_confirm_action)
    except StartupCheckError as exc:
        print(str(exc))
        return 1
    except RubyError as exc:
        print(f"Startup failed: {exc}")
        return 1

    try:
        if context.settings.debug:
            print("Ruby startup checks passed.")
            print(dump_settings_snapshot(context.settings))
        return _interactive_loop(context)
    except KeyboardInterrupt:
        print("\nStopping Ruby.")
        return 0


def init_command(_args: list[str] | None = None) -> int:
    wizard = InitWizard(project_root=PROJECT_ROOT)
    return wizard.run(config_path=DEFAULT_CONFIG_PATH)


def doctor_command(_args: list[str] | None = None) -> int:
    report = run_doctor(DEFAULT_CONFIG_PATH)
    print(report)
    return 0


def models_command(_args: list[str] | None = None) -> int:
    try:
        settings = load_settings(DEFAULT_CONFIG_PATH)
    except RubyError as exc:
        print(f"Config error: {exc}")
        return 1

    whisper_models = discover_whisper_models(
        [
            settings.resolve_path(settings.providers.stt.model).parent,
            PROJECT_ROOT / "whisper.cpp" / "models",
        ]
    )
    print("Whisper models:")
    if whisper_models:
        for model in whisper_models:
            print(f"- {model}")
    else:
        print("- none detected")

    ok, ollama_models, message = discover_ollama_models(settings.providers.llm.url)
    print("Ollama models:")
    if ok and ollama_models:
        for model in ollama_models:
            print(f"- {model}")
    else:
        print(f"- unavailable ({message})")
    return 0


def config_command(_args: list[str] | None = None) -> int:
    try:
        settings = load_settings(DEFAULT_CONFIG_PATH)
    except RubyError as exc:
        print(f"Config error: {exc}")
        return 1

    payload = {
        "settings": json.loads(dump_settings_snapshot(settings)),
        "env": get_env_status(),
        "config_path": str(DEFAULT_CONFIG_PATH),
    }
    print(json.dumps(payload, indent=2))
    return 0


def _print_help() -> None:
    print("Available commands:")
    print("  run     Start Ruby assistant runtime")
    print("  init    Bootstrap environment and local models")
    print("  doctor  Run diagnostics and remediation checks")
    print("  models  List available local STT/LLM models")
    print("  config  Show safe runtime configuration summary")


def dispatch_command(argv: list[str] | None = None) -> int:
    argv = list(argv or [])
    if not argv:
        return run_command([])

    command, *args = argv
    command = command.lower().strip()
    if command == "run":
        return run_command(args)
    if command == "init":
        return init_command(args)
    if command == "doctor":
        return doctor_command(args)
    if command == "models":
        return models_command(args)
    if command == "config":
        return config_command(args)

    print(f"Unknown command: {command}")
    _print_help()
    return 2


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    return dispatch_command(argv)
