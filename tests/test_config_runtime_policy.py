from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from ruby import app
from ruby.config.settings import DEFAULT_CONFIG, load_settings


def test_load_settings_falls_back_to_config_example(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    example_path = tmp_path / "config.example.json"
    example_path.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n", encoding="utf-8")

    settings = load_settings(config_path, load_env=False)
    assert settings.assistant.name == "Ruby"
    assert settings.providers.stt.provider == "whisper_cpp"


def test_runtime_dirs_include_whisper_cpp(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "ruby_workspace"
    fake_settings = SimpleNamespace(workspace_dir=workspace_dir)

    app._ensure_runtime_dirs(tmp_path, fake_settings)

    assert (tmp_path / "recordings").exists()
    assert (tmp_path / "responses").exists()
    assert workspace_dir.exists()
    assert (tmp_path / "whisper.cpp").exists()
