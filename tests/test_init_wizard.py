from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ruby.setup.init_wizard import _to_project_relative_path_string, ensure_env_files


class InitWizardTests(unittest.TestCase):
    def test_ensure_env_files_creates_env_from_example(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            env_example = root / ".env.example"
            env_example.write_text("OPENROUTER_API_KEY=\n", encoding="utf-8")

            ensure_env_files(project_root=root)

            self.assertTrue((root / ".env").exists())
            self.assertEqual((root / ".env").read_text(encoding="utf-8"), "OPENROUTER_API_KEY=\n")

    def test_to_project_relative_path_string_converts_inside_project_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            path = root / "whisper.cpp" / "build" / "bin" / "whisper-cli"

            converted = _to_project_relative_path_string(str(path), root)

            self.assertEqual(converted, "whisper.cpp/build/bin/whisper-cli")


if __name__ == "__main__":
    unittest.main()
