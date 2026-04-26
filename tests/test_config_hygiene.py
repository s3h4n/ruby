from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ruby.config.settings import ConfigError, load_settings


class ConfigHygieneTests(unittest.TestCase):
    def test_config_rejects_inlined_api_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                """
{
  "assistant": {"name": "Ruby", "mode": "text"},
  "providers": {
    "stt": {"provider": "whisper_cpp", "whisper_cli": "whisper.cpp/build/bin/whisper-cli", "model": "whisper.cpp/models/ggml-base.en.bin"},
    "llm": {"provider": "ollama", "model": "llama3.1:8b", "url": "http://localhost:11434/api/chat", "api_key": "secret"},
    "tts": {"provider": "kokoro", "voice": "af_bella"}
  },
  "audio": {"sample_rate": 16000, "record_seconds": 5, "wake_word_enabled": false, "wake_threshold": 0.08, "wake_chunk_size": 1024},
  "security": {"workspace_dir": "ruby_workspace", "shell_enabled": false, "require_confirmation_for_medium_risk": true, "require_confirmation_for_high_risk": true},
  "tools": {"enabled": ["get_time"], "allowed_apps": {"safari": "Safari"}}
}
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_settings(config_path)

    def test_config_rejects_non_boolean_debug(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                """
{
  "assistant": {"name": "Ruby", "mode": "text"},
  "providers": {
    "stt": {"provider": "whisper_cpp", "whisper_cli": "whisper.cpp/build/bin/whisper-cli", "model": "whisper.cpp/models/ggml-base.en.bin"},
    "llm": {"provider": "ollama", "model": "llama3.1:8b", "url": "http://localhost:11434/api/chat"},
    "tts": {"provider": "kokoro", "voice": "af_bella"}
  },
  "audio": {"sample_rate": 16000, "record_seconds": 5, "wake_word_enabled": false, "wake_threshold": 0.08, "wake_chunk_size": 1024},
  "conversation": {"enabled": true, "max_turns": 6},
  "debug": "false",
  "security": {"workspace_dir": "ruby_workspace", "shell_enabled": false, "require_confirmation_for_medium_risk": true, "require_confirmation_for_high_risk": true},
  "tools": {"enabled": ["get_time"], "allowed_apps": {"safari": "Safari"}}
}
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_settings(config_path)

    def test_config_rejects_non_positive_conversation_max_turns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                """
{
  "assistant": {"name": "Ruby", "mode": "text"},
  "providers": {
    "stt": {"provider": "whisper_cpp", "whisper_cli": "whisper.cpp/build/bin/whisper-cli", "model": "whisper.cpp/models/ggml-base.en.bin"},
    "llm": {"provider": "ollama", "model": "llama3.1:8b", "url": "http://localhost:11434/api/chat"},
    "tts": {"provider": "kokoro", "voice": "af_bella"}
  },
  "audio": {"sample_rate": 16000, "record_seconds": 5, "wake_word_enabled": false, "wake_threshold": 0.08, "wake_chunk_size": 1024},
  "conversation": {"enabled": true, "max_turns": 0},
  "debug": false,
  "security": {"workspace_dir": "ruby_workspace", "shell_enabled": false, "require_confirmation_for_medium_risk": true, "require_confirmation_for_high_risk": true},
  "tools": {"enabled": ["get_time"], "allowed_apps": {"safari": "Safari"}}
}
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_settings(config_path)


if __name__ == "__main__":
    unittest.main()
