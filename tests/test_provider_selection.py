from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ruby.config.settings import load_settings
from ruby.providers.factory import build_llm_provider


class ProviderSelectionTests(unittest.TestCase):
    def test_openrouter_provider_requires_env_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text(
                """
{
  "assistant": {"name": "Ruby", "mode": "text"},
  "providers": {
    "stt": {"provider": "whisper_cpp", "whisper_cli": "whisper.cpp/build/bin/whisper-cli", "model": "whisper.cpp/models/ggml-base.en.bin"},
    "llm": {"provider": "openrouter", "model": "openai/gpt-4o-mini", "url": "https://openrouter.ai/api/v1/chat/completions"},
    "tts": {"provider": "kokoro", "voice": "af_bella"}
  },
  "audio": {"sample_rate": 16000, "record_seconds": 5, "wake_word_enabled": false, "wake_threshold": 0.08, "wake_chunk_size": 1024},
  "security": {"workspace_dir": "ruby_workspace", "shell_enabled": false, "require_confirmation_for_medium_risk": true, "require_confirmation_for_high_risk": true},
  "tools": {"enabled": ["get_time"], "allowed_apps": {"safari": "Safari"}}
}
""".strip(),
                encoding="utf-8",
            )

            settings = load_settings(config_path)
            provider = build_llm_provider(settings)
            self.assertEqual(provider.__class__.__name__, "OpenRouterLLMProvider")


if __name__ == "__main__":
    unittest.main()
