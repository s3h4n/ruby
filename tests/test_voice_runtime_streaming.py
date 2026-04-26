from __future__ import annotations

import threading
from pathlib import Path
import time
from types import SimpleNamespace
from unittest.mock import Mock

from ruby.interfaces import cli


def _build_voice_context(tmp_path: Path, *, debug: bool, latency_debug: bool) -> SimpleNamespace:
    recorder = Mock()
    recorder.record.return_value = tmp_path / "recordings" / "command.wav"

    stt_provider = Mock()
    stt_provider.transcribe.return_value = "please summarize this"

    tts_provider = Mock()

    def _synthesize(text: str, output_path: Path) -> Path:
        del text
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"wav")
        return output_path

    tts_provider.synthesize.side_effect = _synthesize

    assistant = Mock()
    assistant.stt_provider = stt_provider
    assistant.tts_provider = tts_provider
    assistant.should_acknowledge_for_voice.return_value = False
    assistant.stream_voice_response.return_value = iter(["Hello there."])
    assistant.finalize_voice_turn.return_value = SimpleNamespace(text="Hello there.")

    player = Mock()
    player.play_with_cancellation.side_effect = lambda _path, cancel_event=None: None

    settings = SimpleNamespace(
        debug=debug,
        providers=SimpleNamespace(llm=SimpleNamespace(provider="ollama")),
        audio=SimpleNamespace(
            recording_mode="fixed",
            record_seconds=1,
            max_turn_seconds=5,
            barge_in_enabled=False,
            min_chunk_words=1,
            max_chunk_words=20,
            max_chunk_wait_ms=500,
            latency_debug=latency_debug,
        ),
    )

    return SimpleNamespace(
        settings=settings,
        recorder=recorder,
        assistant=assistant,
        player=player,
    )


def test_voice_runtime_emits_states_and_latency_when_enabled(tmp_path: Path, monkeypatch, capsys) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=True)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    output = capsys.readouterr().out
    assert result is False
    assert "[Listening]" in output
    assert "[Transcribing]" in output
    assert "[Thinking]" in output
    assert "[Speaking]" in output
    assert "[Done]" in output
    assert "[Latency] speech_end_to_transcript" in output


def test_voice_runtime_suppresses_latency_when_disabled(tmp_path: Path, monkeypatch, capsys) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    output = capsys.readouterr().out
    assert result is False
    assert "[Latency]" not in output


def test_voice_runtime_waits_for_sentence_end_during_token_pause(tmp_path: Path, monkeypatch) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.settings.audio.min_chunk_words = 2
    context.settings.audio.max_chunk_words = 20
    context.settings.audio.max_chunk_wait_ms = 50

    spoken_chunks: list[str] = []

    def _synthesize(text: str, output_path: Path) -> Path:
        spoken_chunks.append(text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"wav")
        return output_path

    context.assistant.tts_provider.synthesize.side_effect = _synthesize

    def _paused_stream() -> object:
        yield "alpha beta gamma"
        time.sleep(0.12)
        yield " delta."

    context.assistant.stream_voice_response.return_value = _paused_stream()
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(text="alpha beta gamma delta.")

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    assert result is False
    assert spoken_chunks == ["alpha beta gamma delta."]


def test_voice_runtime_suppresses_duplicate_final_text_when_captions_cover_response(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    spoken_chunks: list[str] = []

    def _synthesize(text: str, output_path: Path) -> Path:
        spoken_chunks.append(text)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"wav")
        return output_path

    context.assistant.tts_provider.synthesize.side_effect = _synthesize
    markdown_response = "# Title\nUse **bold** and `rm -rf` carefully."
    context.assistant.stream_voice_response.return_value = iter([markdown_response])
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(text=markdown_response)

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    output = capsys.readouterr().out
    spoken_text = " ".join(spoken_chunks)

    assert result is False
    assert "Ruby: Title Use bold and carefully." in output
    assert "**bold**" not in output
    assert "**" not in spoken_text
    assert "`" not in spoken_text
    assert "Title" in spoken_text
    assert "bold" in spoken_text


def test_voice_runtime_prints_only_unseen_residual_text(tmp_path: Path, monkeypatch, capsys) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.assistant.stream_voice_response.return_value = iter(["First sentence. "])
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="First sentence. Second sentence.",
    )

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    output = capsys.readouterr().out
    assert result is False
    assert "Ruby: First sentence." in output
    assert "Ruby: Second sentence." in output
    assert "Ruby: First sentence. Second sentence." not in output


def test_voice_runtime_streams_captions_while_playing_audio(tmp_path: Path, monkeypatch, capsys) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.assistant.stream_voice_response.return_value = iter([
        "Hello world. ",
        "Second sentence.",
    ])
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(text="")

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    output = capsys.readouterr().out
    assert result is False
    assert "Ruby: Hello world." in output
    assert "Ruby: Second sentence." in output


def test_voice_runtime_ignores_barge_in_detection_between_audio_chunks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.settings.audio.barge_in_enabled = True
    context.settings.audio.barge_in_energy_threshold = 0.01

    playing = threading.Event()

    def _play_with_cancellation(_path: Path, cancel_event=None) -> None:
        del cancel_event
        playing.set()
        time.sleep(0.03)
        playing.clear()

    context.player.play_with_cancellation.side_effect = _play_with_cancellation

    def _wait_for_speech(*, cancel_event, stop_event, energy_threshold):
        del energy_threshold
        silence_started_at = None
        while not cancel_event.is_set() and not stop_event.is_set():
            if not playing.is_set():
                if silence_started_at is None:
                    silence_started_at = time.monotonic()
                elif (time.monotonic() - silence_started_at) >= 0.05:
                    return True
            else:
                silence_started_at = None
            time.sleep(0.005)
        return False

    context.recorder.wait_for_speech.side_effect = _wait_for_speech

    def _stream() -> object:
        yield "first chunk. "
        time.sleep(0.12)
        yield "second chunk."

    context.assistant.stream_voice_response.return_value = _stream()
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="first chunk. second chunk.",
    )

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    assert result is False
    context.assistant.finalize_voice_turn.assert_called_once_with(
        "please summarize this",
        "first chunk. second chunk.",
        interrupted=False,
    )


def test_voice_runtime_ignores_immediate_barge_in_spike_near_chunk_start(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.settings.audio.barge_in_enabled = True
    context.settings.audio.barge_in_energy_threshold = 0.01

    context.recorder.wait_for_speech.side_effect = (
        lambda *, cancel_event, stop_event, energy_threshold: True
    )
    context.assistant.stream_voice_response.return_value = iter(["first chunk.", " second chunk."])
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="first chunk. second chunk.",
    )

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    assert result is False
    context.assistant.finalize_voice_turn.assert_called_once_with(
        "please summarize this",
        "first chunk. second chunk.",
        interrupted=False,
    )


def test_voice_runtime_ignores_barge_in_during_first_response_chunk(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.settings.audio.barge_in_enabled = True
    context.settings.audio.barge_in_energy_threshold = 0.01

    playing = threading.Event()

    def _play_with_cancellation(_path: Path, cancel_event=None) -> None:
        del cancel_event
        playing.set()
        time.sleep(0.10)
        playing.clear()

    context.player.play_with_cancellation.side_effect = _play_with_cancellation

    def _wait_for_speech(*, cancel_event, stop_event, energy_threshold):
        del energy_threshold
        while not cancel_event.is_set() and not stop_event.is_set():
            if playing.is_set():
                time.sleep(0.03)
                return True
            time.sleep(0.005)
        return False

    context.recorder.wait_for_speech.side_effect = _wait_for_speech
    context.assistant.stream_voice_response.return_value = iter(["first response chunk."])
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="first response chunk.",
    )

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    assert result is False
    context.assistant.finalize_voice_turn.assert_called_once_with(
        "please summarize this",
        "first response chunk.",
        interrupted=False,
    )


def test_voice_runtime_interrupts_on_barge_in_during_playback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.settings.audio.barge_in_enabled = True
    context.settings.audio.barge_in_energy_threshold = 0.01

    playing = threading.Event()
    play_index = 0

    def _play_with_cancellation(_path: Path, cancel_event=None) -> None:
        nonlocal play_index
        play_index += 1
        playing.set()
        deadline = time.monotonic() + 0.50
        while time.monotonic() < deadline:
            if cancel_event is not None and cancel_event.is_set():
                break
            time.sleep(0.005)
        playing.clear()

    context.player.play_with_cancellation.side_effect = _play_with_cancellation

    def _wait_for_speech(*, cancel_event, stop_event, energy_threshold):
        del energy_threshold
        while not cancel_event.is_set() and not stop_event.is_set():
            if playing.is_set() and play_index >= 2:
                time.sleep(0.03)
                return True
            time.sleep(0.005)
        return False

    context.recorder.wait_for_speech.side_effect = _wait_for_speech
    context.assistant.stream_voice_response.return_value = iter(
        ["first chunk. ", "long chunk that should be interrupted."]
    )
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="first chunk. long chunk that should be interrupted.",
    )

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    assert result is True
    context.assistant.finalize_voice_turn.assert_called_once_with(
        "please summarize this",
        "first chunk. long chunk that should be interrupted.",
        interrupted=True,
    )


def test_voice_runtime_ignores_barge_in_detected_during_acknowledgement_chunk(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    context.settings.audio.barge_in_enabled = True
    context.settings.audio.barge_in_energy_threshold = 0.01
    context.assistant.should_acknowledge_for_voice.return_value = True
    context.assistant.acknowledgement_for_voice.return_value = "Okay, working on that."

    play_index = 0
    playing = threading.Event()

    def _play_with_cancellation(_path: Path, cancel_event=None) -> None:
        nonlocal play_index
        del cancel_event
        play_index += 1
        playing.set()
        time.sleep(0.08)
        playing.clear()

    context.player.play_with_cancellation.side_effect = _play_with_cancellation

    def _wait_for_speech(*, cancel_event, stop_event, energy_threshold):
        del energy_threshold
        while not cancel_event.is_set() and not stop_event.is_set():
            if playing.is_set() and play_index == 1:
                time.sleep(0.03)
                return True
            time.sleep(0.005)
        return False

    context.recorder.wait_for_speech.side_effect = _wait_for_speech
    context.assistant.stream_voice_response.return_value = iter(["first response chunk."])
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="first response chunk.",
    )

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    assert result is False
    context.assistant.finalize_voice_turn.assert_called_once_with(
        "please summarize this",
        "first response chunk.",
        interrupted=False,
    )


def test_voice_runtime_overlaps_playback_before_stream_completion(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    stream_finished = threading.Event()
    playback_started_while_streaming = threading.Event()

    def _play_with_cancellation(_path: Path, cancel_event=None) -> None:
        del cancel_event
        if not stream_finished.is_set():
            playback_started_while_streaming.set()
        time.sleep(0.01)

    context.player.play_with_cancellation.side_effect = _play_with_cancellation

    def _stream() -> object:
        yield "first sentence. "
        time.sleep(0.12)
        yield "second sentence."
        stream_finished.set()

    context.assistant.stream_voice_response.return_value = _stream()
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="first sentence. second sentence.",
    )

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=lambda _timeout: None)

    assert result is False
    assert playback_started_while_streaming.is_set()


def test_voice_runtime_manual_cancel_interrupts_stream_tts_and_playback(
    tmp_path: Path,
    monkeypatch,
) -> None:
    context = _build_voice_context(tmp_path, debug=True, latency_debug=False)
    playback_started = threading.Event()

    def _play_with_cancellation(_path: Path, cancel_event=None) -> None:
        playback_started.set()
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            if cancel_event is not None and cancel_event.is_set():
                break
            time.sleep(0.005)

    context.player.play_with_cancellation.side_effect = _play_with_cancellation

    def _stream() -> object:
        yield "first sentence. "
        time.sleep(0.2)
        yield "second sentence. "
        time.sleep(0.2)
        yield "third sentence."

    context.assistant.stream_voice_response.return_value = _stream()
    context.assistant.finalize_voice_turn.return_value = SimpleNamespace(
        text="first sentence. second sentence. third sentence.",
    )

    cancel_emitted = False

    def _control_poll(_timeout: float) -> str | None:
        nonlocal cancel_emitted
        if playback_started.is_set() and not cancel_emitted:
            cancel_emitted = True
            return "cancel"
        return None

    monkeypatch.setattr(cli, "PROJECT_ROOT", tmp_path)

    result = cli._run_voice_request(context, control_poll_fn=_control_poll)

    assert result is True
    context.assistant.finalize_voice_turn.assert_called_once_with(
        "please summarize this",
        "first sentence.",
        interrupted=True,
    )
