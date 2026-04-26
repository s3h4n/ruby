"""Interactive first-run initialization flow."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Callable

from ruby.config.settings import DEFAULT_CONFIG, DEFAULT_CONFIG_PATH, PROJECT_ROOT
from ruby.setup.model_discovery import (
    discover_ollama_models,
    discover_whisper_binaries,
    discover_whisper_models,
    is_safe_ollama_model_name,
)


ALLOWED_WHISPER_DOWNLOAD_MODELS = {
    "tiny.en",
    "base.en",
    "small.en",
    "medium.en",
}
WHISPER_REPO_URL = "https://github.com/ggerganov/whisper.cpp.git"
ALLOWED_SETUP_EXECUTABLES = {"git", "cmake", "bash", "ollama"}


def _deep_copy_default_config() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_CONFIG))


def _merge_defaults(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(base))

    for key, value in incoming.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            nested_base = merged[key]
            if isinstance(nested_base, dict):
                merged[key] = _merge_defaults(nested_base, value)
            else:
                merged[key] = value
        else:
            merged[key] = value
    return merged


def _to_project_relative_path_string(path_value: str, project_root: Path) -> str:
    if not path_value:
        return path_value

    parsed = Path(path_value)
    if not parsed.is_absolute():
        return path_value

    try:
        return parsed.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path_value


def ensure_env_files(project_root: Path = PROJECT_ROOT) -> tuple[Path, Path]:
    env_example_path = project_root / ".env.example"
    env_path = project_root / ".env"

    if not env_example_path.exists():
        env_example_path.write_text(
            "\n".join(
                [
                    "# Ruby environment values",
                    "# Optional local override for machine-specific whisper model path",
                    "# WHISPER_MODEL_PATH=whisper.cpp/models/ggml-base.en.bin",
                    "OPENROUTER_API_KEY=",
                    "OPENROUTER_BASE_URL=https://openrouter.ai/api/v1",
                    "OPENROUTER_MODEL=",
                    "OPENAI_API_KEY=",
                    "ANTHROPIC_API_KEY=",
                    "RUBY_ENV=development",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    if not env_path.exists():
        env_path.write_text(env_example_path.read_text(encoding="utf-8"), encoding="utf-8")

    return env_example_path, env_path


def _choose_index(
    options: list[str],
    prompt: str,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> int:
    if not options:
        return -1

    if len(options) == 1:
        output_fn(f"Using detected option: {options[0]}")
        return 0

    output_fn(prompt)
    for idx, option in enumerate(options, start=1):
        output_fn(f"  {idx}. {option}")

    while True:
        raw = input_fn("Choose number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        output_fn("Invalid selection. Enter a valid number.")


def _load_raw_config(config_path: Path) -> dict:
    default = _deep_copy_default_config()
    if not config_path.exists():
        return default
    try:
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            return default
        return _merge_defaults(default, loaded)
    except json.JSONDecodeError:
        return default


def _download_whisper_model(project_root: Path, model_name: str) -> tuple[bool, str]:
    if model_name not in ALLOWED_WHISPER_DOWNLOAD_MODELS:
        return False, f"Model '{model_name}' is not in the allowed download list."

    script_path = project_root / "whisper.cpp" / "models" / "download-ggml-model.sh"
    if not script_path.exists():
        return False, f"Missing download script at {script_path}."

    ok, details = _run_allowlisted_command(["bash", str(script_path), model_name])
    if not ok:
        return False, f"Failed to download model: {details}"
    return True, "Whisper model downloaded successfully."


def _run_allowlisted_command(command: list[str], cwd: Path | None = None) -> tuple[bool, str]:
    if not command:
        return False, "No command provided."

    executable = Path(command[0]).name
    if executable not in ALLOWED_SETUP_EXECUTABLES:
        return False, f"Blocked setup command '{executable}'. Only allowlisted setup commands are permitted."

    result = subprocess.run(command, cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return True, result.stdout.strip() or "OK"
    details = result.stderr.strip() or result.stdout.strip() or "unknown error"
    return False, details


def _ensure_whisper_repo(project_root: Path, output_fn: Callable[[str], None]) -> tuple[bool, Path]:
    whisper_dir = project_root / "whisper.cpp"
    git_dir = whisper_dir / ".git"
    if git_dir.exists():
        return True, whisper_dir

    output_fn("whisper.cpp repository not found; cloning...")
    ok, message = _run_allowlisted_command(
        ["git", "clone", WHISPER_REPO_URL, str(whisper_dir)],
        cwd=project_root,
    )
    if not ok:
        output_fn(f"Failed to clone whisper.cpp: {message}")
        return False, whisper_dir
    output_fn("Cloned whisper.cpp successfully.")
    return True, whisper_dir


def _ensure_whisper_built(whisper_dir: Path, output_fn: Callable[[str], None]) -> tuple[bool, Path]:
    whisper_cli = whisper_dir / "build" / "bin" / "whisper-cli"
    if whisper_cli.exists():
        return True, whisper_cli

    output_fn("whisper.cpp binary not found; building...")
    configure_ok, configure_message = _run_allowlisted_command(
        ["cmake", "-S", str(whisper_dir), "-B", str(whisper_dir / "build")],
        cwd=whisper_dir,
    )
    if not configure_ok:
        output_fn(f"whisper.cpp configure failed: {configure_message}")
        return False, whisper_cli

    build_ok, build_message = _run_allowlisted_command(
        ["cmake", "--build", str(whisper_dir / "build"), "-j"],
        cwd=whisper_dir,
    )
    if not build_ok:
        output_fn(f"whisper.cpp build failed: {build_message}")
        return False, whisper_cli

    if not whisper_cli.exists():
        output_fn("Build completed but whisper-cli was not found in expected path.")
        return False, whisper_cli
    output_fn("Built whisper.cpp successfully.")
    return True, whisper_cli


def _ollama_pull_model(model_name: str) -> tuple[bool, str]:
    if not is_safe_ollama_model_name(model_name):
        return False, "Ollama model name contains unsafe characters."

    ok, message = _run_allowlisted_command(["ollama", "pull", model_name])
    if not ok:
        return False, f"Failed to pull Ollama model: {message}"
    return True, f"Pulled Ollama model: {model_name}"


class InitWizard:
    """Guided setup for first-run open-source onboarding."""

    def __init__(
        self,
        project_root: Path = PROJECT_ROOT,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self.project_root = project_root
        self.input_fn = input_fn
        self.output_fn = output_fn

    def run(self, config_path: Path = DEFAULT_CONFIG_PATH) -> int:
        self.output_fn("Ruby init wizard")
        ensure_env_files(self.project_root)

        raw = _load_raw_config(config_path)

        whisper_repo_ok, whisper_dir = _ensure_whisper_repo(self.project_root, self.output_fn)
        if not whisper_repo_ok:
            return 1

        whisper_built_ok, built_whisper_cli = _ensure_whisper_built(whisper_dir, self.output_fn)
        if whisper_built_ok:
            raw["providers"]["stt"]["whisper_cli"] = _to_project_relative_path_string(
                str(built_whisper_cli),
                self.project_root,
            )

        whisper_cli_candidates = discover_whisper_binaries(
            [
                Path(raw.get("providers", {}).get("stt", {}).get("whisper_cli", "")),
                self.project_root / "whisper.cpp" / "build" / "bin" / "whisper-cli",
            ]
        )
        if whisper_cli_candidates:
            options = [
                _to_project_relative_path_string(str(path), self.project_root)
                for path in whisper_cli_candidates
            ]
            choice = _choose_index(
                options,
                "Select whisper-cli path:",
                self.input_fn,
                self.output_fn,
            )
            raw["providers"]["stt"]["whisper_cli"] = options[choice]
        else:
            manual = self.input_fn("Enter whisper-cli path: ").strip()
            raw["providers"]["stt"]["whisper_cli"] = _to_project_relative_path_string(
                manual,
                self.project_root,
            )

        whisper_model_dirs = [
            Path(raw.get("providers", {}).get("stt", {}).get("model", "")).parent,
            self.project_root / "whisper.cpp" / "models",
        ]
        whisper_models = discover_whisper_models(whisper_model_dirs)
        if not whisper_models:
            download = self.input_fn(
                "No whisper model found. Download one now? [y/N]: "
            ).strip().lower()
            if download in {"y", "yes"}:
                model_name = self.input_fn(
                    "Enter model name (tiny.en/base.en/small.en/medium.en): "
                ).strip()
                ok, message = _download_whisper_model(self.project_root, model_name)
                self.output_fn(message)
                if ok:
                    whisper_models = discover_whisper_models(whisper_model_dirs)

        if whisper_models:
            options = [
                _to_project_relative_path_string(str(path), self.project_root)
                for path in whisper_models
            ]
            choice = _choose_index(
                options,
                "Select whisper model:",
                self.input_fn,
                self.output_fn,
            )
            raw["providers"]["stt"]["model"] = options[choice]

        llm_url = str(raw.get("providers", {}).get("llm", {}).get("url", ""))
        ok, ollama_models, ollama_message = discover_ollama_models(llm_url)
        if not ok:
            self.output_fn(f"Ollama discovery warning: {ollama_message}")
        if not ollama_models:
            pull = self.input_fn("No Ollama models detected. Pull one now? [y/N]: ").strip().lower()
            if pull in {"y", "yes"}:
                model_name = self.input_fn("Enter Ollama model to pull: ").strip()
                pull_ok, pull_message = _ollama_pull_model(model_name)
                self.output_fn(pull_message)
                if pull_ok:
                    ok, ollama_models, _ = discover_ollama_models(llm_url)

        if ollama_models:
            choice = _choose_index(
                ollama_models,
                "Select Ollama model:",
                self.input_fn,
                self.output_fn,
            )
            raw["providers"]["llm"]["model"] = ollama_models[choice]

        self._ensure_runtime_dirs(raw)
        config_path.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
        self.output_fn(f"Wrote configuration to {config_path}")
        self.output_fn("Init complete. Next: run `python app.py doctor` then `python app.py run`.")
        return 0

    def _ensure_runtime_dirs(self, raw_config: dict) -> None:
        workspace_dir = Path(raw_config.get("security", {}).get("workspace_dir", "ruby_workspace"))
        if not workspace_dir.is_absolute():
            workspace_dir = (self.project_root / workspace_dir).resolve()
        (self.project_root / "recordings").mkdir(parents=True, exist_ok=True)
        (self.project_root / "responses").mkdir(parents=True, exist_ok=True)
        (self.project_root / "whisper.cpp").mkdir(parents=True, exist_ok=True)
        workspace_dir.mkdir(parents=True, exist_ok=True)
