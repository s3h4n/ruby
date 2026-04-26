from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ruby.config.settings import load_settings


class ConfigMigrationTests(unittest.TestCase):
    def test_legacy_config_is_migrated_with_defaults(self) -> None:
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
  "audio": {"sample_rate": 16000, "record_seconds": 5},
  "security": {"workspace_dir": "ruby_workspace", "shell_enabled": false},
  "tools": {"enabled": ["get_time"], "allowed_apps": {"safari": "Safari"}}
}
""".strip(),
                encoding="utf-8",
            )

            settings = load_settings(config_path)
            self.assertEqual(settings.audio.wake_chunk_size, 1024)
            self.assertTrue(settings.security.require_confirmation_for_medium_risk)
            self.assertTrue(settings.conversation.enabled)
            self.assertEqual(settings.conversation.max_turns, 6)
            self.assertFalse(settings.debug)

            migrated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertIn("wake_word_enabled", migrated["audio"])
            self.assertIn("require_confirmation_for_high_risk", migrated["security"])
            self.assertIn("conversation", migrated)
            self.assertIn("debug", migrated)

    def test_project_absolute_stt_paths_are_normalized_to_relative(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            whisper_cli = root / "whisper.cpp" / "build" / "bin" / "whisper-cli"
            whisper_model = root / "whisper.cpp" / "models" / "ggml-base.en.bin"
            config_path = root / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "assistant": {"name": "Ruby", "mode": "text"},
                        "providers": {
                            "stt": {
                                "provider": "whisper_cpp",
                                "whisper_cli": str(whisper_cli),
                                "model": str(whisper_model),
                            },
                            "llm": {
                                "provider": "ollama",
                                "model": "llama3.1:8b",
                                "url": "http://localhost:11434/api/chat",
                            },
                            "tts": {"provider": "kokoro", "voice": "af_bella"},
                        },
                        "audio": {"sample_rate": 16000, "record_seconds": 5},
                        "security": {"workspace_dir": "ruby_workspace", "shell_enabled": False},
                        "tools": {"enabled": ["get_time"], "allowed_apps": {"safari": "Safari"}},
                    }
                ),
                encoding="utf-8",
            )

            settings = load_settings(config_path)

            migrated = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(
                migrated["providers"]["stt"]["whisper_cli"],
                "whisper.cpp/build/bin/whisper-cli",
            )
            self.assertEqual(
                migrated["providers"]["stt"]["model"],
                "whisper.cpp/models/ggml-base.en.bin",
            )
            self.assertEqual(settings.providers.stt.model, "whisper.cpp/models/ggml-base.en.bin")


if __name__ == "__main__":
    unittest.main()
