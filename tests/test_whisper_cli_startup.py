from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from ruby import app
from ruby.core.errors import StartupCheckError


class _FakeSettings:
    def __init__(self, whisper_cli: Path, model_path: Path) -> None:
        self.providers = SimpleNamespace(
            stt=SimpleNamespace(
                whisper_cli=str(whisper_cli),
                model=str(model_path),
            ),
            llm=SimpleNamespace(url="http://localhost:11434/api/chat"),
        )

    def resolve_path(self, value: str) -> Path:
        return Path(value)


class _FakeRecorder:
    def check_microphone_access(self) -> None:
        return None


class WhisperCliStartupValidationTests(unittest.TestCase):
    def test_startup_checks_fail_when_whisper_cli_has_missing_dylib(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            whisper_cli = root / "whisper-cli"
            whisper_cli.write_text(
                "#!/bin/sh\n"
                "echo 'dyld[1]: Library not loaded: @rpath/libwhisper.1.dylib' 1>&2\n"
                "exit 1\n",
                encoding="utf-8",
            )
            os.chmod(whisper_cli, 0o755)

            model_path = root / "model.bin"
            model_path.write_text("model", encoding="utf-8")

            settings = _FakeSettings(whisper_cli, model_path)
            recorder = _FakeRecorder()

            with mock.patch("ruby.app._check_ollama_connectivity"), mock.patch(
                "ruby.app.importlib.import_module",
                return_value=object(),
            ):
                with self.assertRaises(StartupCheckError) as context:
                    app._run_startup_checks(settings, recorder)

        message = str(context.exception).lower()
        self.assertIn("libwhisper", message)
        self.assertIn("rebuild whisper.cpp", message)


if __name__ == "__main__":
    unittest.main()
