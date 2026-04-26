from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_root_app_delegates_to_ruby_cli() -> None:
    app_contents = (REPO_ROOT / "app.py").read_text(encoding="utf-8")
    assert "from ruby.cli import main" in app_contents
    assert "ruby.interfaces.cli" not in app_contents


def test_python_module_execution_entrypoint_exists() -> None:
    module = importlib.import_module("ruby.__main__")
    assert hasattr(module, "main")


def test_unknown_command_parity_between_app_and_module() -> None:
    app_result = subprocess.run(
        [sys.executable, "app.py", "nope"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    module_result = subprocess.run(
        [sys.executable, "-m", "ruby", "nope"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert app_result.returncode == 2
    assert module_result.returncode == 2
    assert "Unknown command" in app_result.stdout
    assert "Unknown command" in module_result.stdout
    assert "Available commands" in app_result.stdout
    assert "Available commands" in module_result.stdout
