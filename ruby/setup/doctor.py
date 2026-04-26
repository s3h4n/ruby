"""Doctor diagnostics command implementation."""

from __future__ import annotations

import importlib
import os
import subprocess
from pathlib import Path

from ruby.audio.recorder import AudioRecorder
from ruby.config.settings import DEFAULT_CONFIG_PATH, load_settings
from ruby.core.errors import ConfigError
from ruby.setup.model_discovery import discover_ollama_models


def check_ollama_tags(chat_url: str = "http://localhost:11434/api/chat") -> tuple[bool, str]:
    ok, models, message = discover_ollama_models(chat_url)
    if not ok:
        return False, f"{message}. Start Ollama and run `ollama pull llama3.1:8b`."
    if not models:
        return False, "No Ollama models found. Pull one with `ollama pull llama3.1:8b`."
    return True, f"Detected models: {', '.join(models)}"


def _check_whisper_cli(whisper_cli: Path) -> tuple[bool, str]:
    if not whisper_cli.exists():
        return False, f"Missing whisper-cli at {whisper_cli}. Build whisper.cpp in this workspace."
    result = subprocess.run([str(whisper_cli), "--help"], capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return True, f"whisper-cli runnable at {whisper_cli}"
    details = result.stderr.strip() or result.stdout.strip() or "unknown error"
    return False, f"whisper-cli failed startup: {details.splitlines()[0]}"


def run_doctor(config_path: Path | None = None) -> str:
    lines: list[str] = ["Ruby doctor report"]
    config_path = config_path or DEFAULT_CONFIG_PATH

    try:
        settings = load_settings(config_path)
        lines.append(f"PASS config: loaded {config_path}")
    except ConfigError as exc:
        lines.append(f"FAIL config: {exc}")
        lines.append("Remediation: run `python app.py init`.")
        return "\n".join(lines)

    env_path = config_path.parent / ".env"
    if env_path.exists():
        lines.append(f"PASS env: found {env_path}")
    else:
        lines.append(f"FAIL env: missing {env_path}")
        lines.append("Remediation: run `python app.py init` to bootstrap .env.")

    whisper_cli = settings.resolve_path(settings.providers.stt.whisper_cli)
    whisper_ok, whisper_message = _check_whisper_cli(whisper_cli)
    lines.append(("PASS whisper-cli: " if whisper_ok else "FAIL whisper-cli: ") + whisper_message)

    whisper_model = settings.resolve_path(settings.providers.stt.model)
    if whisper_model.exists():
        lines.append(f"PASS whisper-model: found {whisper_model}")
    else:
        lines.append(f"FAIL whisper-model: missing {whisper_model}")
        lines.append("Remediation: download or select a model via `python app.py init`.")

    runtime_dirs = [
        config_path.parent / "recordings",
        config_path.parent / "responses",
        config_path.parent / "whisper.cpp",
        settings.workspace_dir,
    ]
    for runtime_dir in runtime_dirs:
        if runtime_dir.exists() and runtime_dir.is_dir():
            lines.append(f"PASS runtime-dir: found {runtime_dir}")
        else:
            lines.append(f"FAIL runtime-dir: missing {runtime_dir}")
            lines.append("Remediation: run `python app.py init` to create runtime directories.")

    if settings.providers.stt.provider != "whisper_cpp":
        lines.append(
            "FAIL stt-provider: unsupported provider "
            f"'{settings.providers.stt.provider}'."
        )
        lines.append("Remediation: set providers.stt.provider to 'whisper_cpp'.")

    if settings.providers.llm.provider == "ollama":
        ollama_ok, ollama_message = check_ollama_tags(settings.providers.llm.url)
        lines.append(("PASS ollama: " if ollama_ok else "FAIL ollama: ") + ollama_message)
        if not ollama_ok:
            lines.append("Remediation: Start Ollama and pull the configured model.")
    elif settings.providers.llm.provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if api_key:
            lines.append("PASS openrouter-api-key: OPENROUTER_API_KEY is set")
        else:
            lines.append("FAIL openrouter-api-key: OPENROUTER_API_KEY is missing")
            lines.append("Remediation: set OPENROUTER_API_KEY in .env before using OpenRouter.")
    else:
        lines.append(
            "FAIL llm-provider: unsupported provider "
            f"'{settings.providers.llm.provider}'."
        )
        lines.append("Remediation: set providers.llm.provider to 'ollama' or 'openrouter'.")

    if settings.providers.tts.provider == "kokoro":
        try:
            importlib.import_module("kokoro")
            lines.append("PASS kokoro: import successful")
        except ModuleNotFoundError:
            lines.append("FAIL kokoro: package not importable")
            lines.append("Remediation: install Kokoro in the active virtual environment.")
    else:
        lines.append(
            "FAIL tts-provider: unsupported provider "
            f"'{settings.providers.tts.provider}'."
        )
        lines.append("Remediation: set providers.tts.provider to 'kokoro'.")

    recorder = AudioRecorder(sample_rate=settings.audio.sample_rate)
    try:
        recorder.check_microphone_access()
        lines.append("PASS microphone: input device available")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"FAIL microphone: {exc}")
        lines.append(
            "Remediation: grant microphone permission in macOS Privacy settings and retry."
        )

    return "\n".join(lines)
