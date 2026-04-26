from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from ruby.config.settings import load_settings
from ruby.core.errors import RubyError
from ruby.core.pipeline import build_system_prompt
from ruby.interfaces import cli


class _FakeToolRegistry:
    def describe_enabled_tools(self) -> str:
        return "- get_time"


def test_build_system_prompt_uses_external_template(tmp_path: Path) -> None:
    prompt_file = tmp_path / "system_prompt.md"
    prompt_file.write_text(
        "You are Ruby.\\nEnabled tools:\\n{{enabled_tools}}\\n",
        encoding="utf-8",
    )

    prompt = build_system_prompt(_FakeToolRegistry(), prompt_path=prompt_file)

    assert "You are Ruby." in prompt
    assert "- get_time" in prompt


def test_build_system_prompt_missing_file_raises_clear_error(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_prompt.md"

    with pytest.raises(RubyError) as exc:
        build_system_prompt(_FakeToolRegistry(), prompt_path=missing_path)

    assert "prompt" in str(exc.value).lower()
    assert "missing_prompt.md" in str(exc.value)


def test_load_settings_applies_whisper_model_env_override(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        """
{
  "assistant": {"name": "Ruby", "mode": "voice"},
  "providers": {
    "stt": {"provider": "whisper_cpp", "whisper_cli": "whisper.cpp/build/bin/whisper-cli", "model": "whisper.cpp/models/ggml-base.en.bin"},
    "llm": {"provider": "ollama", "model": "llama3.1:8b", "url": "http://localhost:11434/api/chat"},
    "tts": {"provider": "kokoro", "voice": "af_bella"}
  },
  "audio": {"sample_rate": 16000, "record_seconds": 1, "wake_word_enabled": false, "wake_threshold": 0.08, "wake_chunk_size": 1024},
  "conversation": {"enabled": true, "max_turns": 6},
  "debug": false,
  "security": {"workspace_dir": "ruby_workspace", "shell_enabled": false, "require_confirmation_for_medium_risk": true, "require_confirmation_for_high_risk": true},
  "tools": {"enabled": ["get_time"], "allowed_apps": {"safari": "Safari"}}
}
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("WHISPER_MODEL_PATH", "/tmp/custom-model.bin")

    settings = load_settings(config_path, load_env=False)

    assert settings.providers.stt.model == "/tmp/custom-model.bin"


def test_run_text_request_interrupt_returns_cleanly(capsys) -> None:
    context = SimpleNamespace(
        settings=SimpleNamespace(debug=False, providers=SimpleNamespace(llm=SimpleNamespace(provider="ollama"))),
        assistant=Mock(),
        player=Mock(),
    )

    def delayed_handle_text(_text: str):
        time.sleep(0.2)
        return SimpleNamespace(text="Hello", warning="", audio_path="")

    context.assistant.handle_text.side_effect = delayed_handle_text

    cancel_event = threading.Event()
    cli._run_text_request(
        context,
        "hello",
        cancel_event=cancel_event,
        control_poll_fn=lambda _timeout: "cancel",
    )

    output = capsys.readouterr().out
    assert "[Interrupted]" in output
    context.player.play.assert_not_called()
