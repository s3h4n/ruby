"""Config loading and typed settings models for Ruby."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ruby.core.compat import compat_dataclass
from ruby.core.errors import ConfigError


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"
DEFAULT_CONFIG_EXAMPLE_PATH = PROJECT_ROOT / "config.example.json"
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"


DEFAULT_CONFIG: dict[str, Any] = {
    "assistant": {
        "name": "Ruby",
        "mode": "voice",
    },
    "providers": {
        "stt": {
            "provider": "whisper_cpp",
            "whisper_cli": "whisper.cpp/build/bin/whisper-cli",
            "model": "whisper.cpp/models/ggml-base.en.bin",
        },
        "llm": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "url": "http://localhost:11434/api/chat",
        },
        "tts": {
            "provider": "kokoro",
            "voice": "af_bella",
        },
    },
    "audio": {
        "sample_rate": 16000,
        "record_seconds": 5,
        "wake_word_enabled": True,
        "wake_threshold": 0.08,
        "wake_chunk_size": 1024,
    },
    "conversation": {
        "enabled": True,
        "max_turns": 6,
    },
    "debug": False,
    "security": {
        "workspace_dir": "ruby_workspace",
        "shell_enabled": False,
        "require_confirmation_for_medium_risk": True,
        "require_confirmation_for_high_risk": True,
    },
    "tools": {
        "enabled": [
            "get_time",
            "open_app",
            "list_directory",
            "create_folder",
            "create_file",
        ],
        "allowed_apps": {
            "chrome": "Google Chrome",
            "safari": "Safari",
            "notes": "Notes",
            "calendar": "Calendar",
            "terminal": "Terminal",
        },
    },
}


@compat_dataclass(slots=True)
class AssistantConfig:
    name: str
    mode: str


@compat_dataclass(slots=True)
class STTConfig:
    provider: str
    whisper_cli: str
    model: str


@compat_dataclass(slots=True)
class LLMConfig:
    provider: str
    model: str
    url: str


@compat_dataclass(slots=True)
class TTSConfig:
    provider: str
    voice: str


@compat_dataclass(slots=True)
class ProvidersConfig:
    stt: STTConfig
    llm: LLMConfig
    tts: TTSConfig


@compat_dataclass(slots=True)
class AudioConfig:
    sample_rate: int
    record_seconds: int
    wake_word_enabled: bool
    wake_threshold: float
    wake_chunk_size: int


@compat_dataclass(slots=True)
class ConversationConfig:
    enabled: bool
    max_turns: int


@compat_dataclass(slots=True)
class SecurityConfig:
    workspace_dir: str
    shell_enabled: bool
    require_confirmation_for_medium_risk: bool
    require_confirmation_for_high_risk: bool


@compat_dataclass(slots=True)
class ToolsConfig:
    enabled: list[str]
    allowed_apps: dict[str, str]


@compat_dataclass(slots=True)
class Settings:
    assistant: AssistantConfig
    providers: ProvidersConfig
    audio: AudioConfig
    conversation: ConversationConfig
    debug: bool
    security: SecurityConfig
    tools: ToolsConfig

    def resolve_path(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (PROJECT_ROOT / path).resolve()

    @property
    def workspace_dir(self) -> Path:
        return self.resolve_path(self.security.workspace_dir)


def resolve_project_path(value: str, project_root: Path = PROJECT_ROOT) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def _require(data: dict[str, Any], key: str, section: str) -> Any:
    if key not in data:
        raise ConfigError(f"Missing '{key}' in config section '{section}'.")
    return data[key]


def _deep_copy(data: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(data))


def _require_bool(data: dict[str, Any], key: str, section: str) -> bool:
    value = _require(data, key, section)
    if type(value) is not bool:
        raise ConfigError(
            f"Invalid '{key}' in config section '{section}'. Expected a boolean."
        )
    return value


def _require_positive_int(data: dict[str, Any], key: str, section: str) -> int:
    value = _require(data, key, section)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(
            f"Invalid '{key}' in config section '{section}'. Expected a positive integer."
        )
    if value <= 0:
        raise ConfigError(
            f"Invalid '{key}' in config section '{section}'. Expected a value greater than 0."
        )
    return value


def _merge_defaults(raw: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    merged = _deep_copy(raw)
    for key, default_value in defaults.items():
        if key not in merged:
            merged[key] = _deep_copy(default_value) if isinstance(default_value, dict) else default_value
            continue

        if isinstance(default_value, dict) and isinstance(merged[key], dict):
            merged[key] = _merge_defaults(merged[key], default_value)
    return merged


def _find_inline_secret_field(data: Any, path: str = "") -> str:
    forbidden_keys = {"api_key", "token", "secret", "password"}
    if isinstance(data, dict):
        for key, value in data.items():
            child_path = f"{path}.{key}" if path else key
            if key.lower() in forbidden_keys and str(value).strip():
                return child_path
            found = _find_inline_secret_field(value, child_path)
            if found:
                return found
    if isinstance(data, list):
        for idx, item in enumerate(data):
            found = _find_inline_secret_field(item, f"{path}[{idx}]")
            if found:
                return found
    return ""


def _load_dotenv_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv
    except ModuleNotFoundError as exc:
        raise ConfigError(
            "Missing dependency 'python-dotenv'. Install project dependencies first."
        ) from exc
    load_dotenv(dotenv_path=env_path, override=False)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _apply_environment_overrides(merged: dict[str, Any]) -> None:
    whisper_model_override = os.getenv("WHISPER_MODEL_PATH", "").strip()
    if whisper_model_override:
        providers = merged.setdefault("providers", {})
        stt = providers.setdefault("stt", {})
        stt["model"] = whisper_model_override


def _normalize_project_local_paths(merged: dict[str, Any], project_root: Path) -> None:
    providers = merged.get("providers", {})
    stt = providers.get("stt", {})
    for field in ("whisper_cli", "model"):
        raw_value = stt.get(field)
        if not isinstance(raw_value, str) or not raw_value:
            continue

        value_path = Path(raw_value)
        if not value_path.is_absolute():
            continue

        try:
            relative_path = value_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            continue

        stt[field] = relative_path.as_posix()


def _resolve_config_source(config_path: Path) -> tuple[Path, bool]:
    if config_path.exists():
        return config_path, True

    fallback_path = config_path.with_name("config.example.json")
    if fallback_path.exists():
        return fallback_path, False

    raise ConfigError(
        "Missing config file and fallback defaults: "
        f"{config_path} and {fallback_path}. "
        "Run `python app.py init` to bootstrap configuration."
    )


def load_settings(
    config_path: Path | None = None,
    *,
    auto_migrate: bool = True,
    load_env: bool = True,
) -> Settings:
    config_path = config_path or DEFAULT_CONFIG_PATH
    source_path, using_primary_config = _resolve_config_source(config_path)

    try:
        raw = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {source_path}: {exc}") from exc

    forbidden_path = _find_inline_secret_field(raw)
    if forbidden_path:
        raise ConfigError(
            f"Inline secrets are not allowed in config.json ({forbidden_path}). "
            "Move secret values to .env."
        )

    merged = _merge_defaults(raw, DEFAULT_CONFIG)
    _normalize_project_local_paths(merged, config_path.parent)
    if auto_migrate and using_primary_config and merged != raw:
        _write_json(config_path, merged)

    if load_env:
        _load_dotenv_file(config_path.parent / ".env")
    _apply_environment_overrides(merged)

    assistant_raw = _require(merged, "assistant", "root")
    providers_raw = _require(merged, "providers", "root")
    audio_raw = _require(merged, "audio", "root")
    conversation_raw = _require(merged, "conversation", "root")
    debug_raw = _require_bool(merged, "debug", "root")
    security_raw = _require(merged, "security", "root")
    tools_raw = _require(merged, "tools", "root")

    stt_raw = _require(providers_raw, "stt", "providers")
    llm_raw = _require(providers_raw, "llm", "providers")
    tts_raw = _require(providers_raw, "tts", "providers")

    settings = Settings(
        assistant=AssistantConfig(
            name=str(_require(assistant_raw, "name", "assistant")),
            mode=str(_require(assistant_raw, "mode", "assistant")),
        ),
        providers=ProvidersConfig(
            stt=STTConfig(
                provider=str(_require(stt_raw, "provider", "providers.stt")),
                whisper_cli=str(_require(stt_raw, "whisper_cli", "providers.stt")),
                model=str(_require(stt_raw, "model", "providers.stt")),
            ),
            llm=LLMConfig(
                provider=str(_require(llm_raw, "provider", "providers.llm")),
                model=str(_require(llm_raw, "model", "providers.llm")),
                url=str(_require(llm_raw, "url", "providers.llm")),
            ),
            tts=TTSConfig(
                provider=str(_require(tts_raw, "provider", "providers.tts")),
                voice=str(_require(tts_raw, "voice", "providers.tts")),
            ),
        ),
        audio=AudioConfig(
            sample_rate=int(_require(audio_raw, "sample_rate", "audio")),
            record_seconds=int(_require(audio_raw, "record_seconds", "audio")),
            wake_word_enabled=bool(_require(audio_raw, "wake_word_enabled", "audio")),
            wake_threshold=float(_require(audio_raw, "wake_threshold", "audio")),
            wake_chunk_size=int(_require(audio_raw, "wake_chunk_size", "audio")),
        ),
        conversation=ConversationConfig(
            enabled=_require_bool(conversation_raw, "enabled", "conversation"),
            max_turns=_require_positive_int(conversation_raw, "max_turns", "conversation"),
        ),
        debug=debug_raw,
        security=SecurityConfig(
            workspace_dir=str(_require(security_raw, "workspace_dir", "security")),
            shell_enabled=bool(_require(security_raw, "shell_enabled", "security")),
            require_confirmation_for_medium_risk=bool(
                _require(
                    security_raw,
                    "require_confirmation_for_medium_risk",
                    "security",
                )
            ),
            require_confirmation_for_high_risk=bool(
                _require(
                    security_raw,
                    "require_confirmation_for_high_risk",
                    "security",
                )
            ),
        ),
        tools=ToolsConfig(
            enabled=list(_require(tools_raw, "enabled", "tools")),
            allowed_apps=dict(_require(tools_raw, "allowed_apps", "tools")),
        ),
    )
    return settings


def get_env_status() -> dict[str, bool]:
    return {
        "OPENROUTER_API_KEY": bool(os.getenv("OPENROUTER_API_KEY", "").strip()),
    }
