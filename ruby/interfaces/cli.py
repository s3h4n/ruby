"""CLI interface for Ruby assistant."""

from __future__ import annotations

import json
import os
import select
import sys
import threading
import time
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
from ruby.setup.doctor import run_doctor
from ruby.setup.init_wizard import InitWizard
from ruby.setup.model_discovery import discover_ollama_models, discover_whisper_models


AVAILABLE_COMMANDS = ("run", "init", "doctor", "models", "config")


STATE_READY = "[Ready]"
STATE_RECORDING = "[Recording]"
STATE_RECORDED = "[Recorded]"
STATE_TRANSCRIBING = "[Transcribing]"
STATE_THINKING = "[Thinking]"
STATE_SPEAKING = "[Speaking]"
STATE_DONE = "[Done]"
STATE_INTERRUPTED = "[Interrupted]"

ControlPollFn = Callable[[float], str | None]


def _print_state(label: str, message: str = "") -> None:
    if message:
        print(f"{label} {message}")
        return
    print(label)


def _print_debug(context: AppContext, label: str, details: str) -> None:
    if not context.settings.debug:
        return
    print(f"[Debug] {label}: {details}")


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

    _print_state(STATE_RECORDING)

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

    _print_state(STATE_RECORDED)
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

    if interrupted or cancel_event.is_set() or not transcript:
        _print_state(STATE_INTERRUPTED)
        _print_state(STATE_READY)
        return True

    return _run_text_request(
        context,
        transcript,
        cancel_event=cancel_event,
        control_poll_fn=control_poll,
    )


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
