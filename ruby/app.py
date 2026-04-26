"""Application assembly and startup validation."""

from __future__ import annotations

import importlib
import io
import json
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Callable

from ruby.audio.player import AudioPlayer
from ruby.audio.recorder import AudioRecorder
from ruby.audio.wake import WakeWordDetector
from ruby.config.settings import DEFAULT_CONFIG_PATH, PROJECT_ROOT, Settings, load_settings
from ruby.core.assistant import RubyAssistant
from ruby.core.compat import compat_dataclass
from ruby.core.errors import StartupCheckError
from ruby.core.schemas import ToolDefinition
from ruby.providers.factory import (
    build_llm_provider,
    build_search_provider,
    build_stt_provider,
    build_tts_provider,
)
from ruby.security.command_policy import CommandPolicy
from ruby.security.permissions import RiskPermissionPolicy, WorkspaceGuard
from ruby.tools.files import FileTools
from ruby.tools.registry import ToolRegistry
from ruby.tools.shell_tools import ShellTools
from ruby.tools.system import SystemTools


@compat_dataclass(slots=True)
class AppContext:
    settings: Settings
    assistant: RubyAssistant
    recorder: AudioRecorder
    player: AudioPlayer
    wake_detector: WakeWordDetector


def _ensure_runtime_dirs(project_root: Path, settings: Settings) -> None:
    (project_root / "recordings").mkdir(parents=True, exist_ok=True)
    (project_root / "responses").mkdir(parents=True, exist_ok=True)
    (project_root / "whisper.cpp").mkdir(parents=True, exist_ok=True)
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)


def _check_ollama_connectivity(chat_url: str) -> None:
    parsed = urllib.parse.urlparse(chat_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    tags_url = f"{base}/api/tags"
    request = urllib.request.Request(tags_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            _ = response.read()
    except urllib.error.URLError as exc:
        raise StartupCheckError(
            "Cannot reach Ollama API endpoint. Start Ollama and ensure the API is reachable."
        ) from exc


def _check_whisper_cli_runtime(whisper_cli: Path) -> None:
    try:
        result = subprocess.run(
            [str(whisper_cli), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise StartupCheckError(
            "whisper-cli could not be executed. Rebuild whisper.cpp in this workspace "
            "and update providers.stt.whisper_cli if needed."
        ) from exc

    if result.returncode == 0:
        return

    details = (result.stderr.strip() or result.stdout.strip() or "unknown error").strip()
    lowered = details.lower()
    if "library not loaded" in lowered or "libwhisper" in lowered:
        raise StartupCheckError(
            "whisper-cli failed to start because required whisper.cpp dynamic libraries "
            "could not be loaded (libwhisper). Rebuild whisper.cpp in this workspace and "
            "point providers.stt.whisper_cli to that rebuilt binary."
        )

    first_line = details.splitlines()[0] if details else "unknown error"
    raise StartupCheckError(
        f"whisper-cli failed startup check: {first_line}. "
        "Run whisper.cpp build again and verify the configured binary path."
    )


def _run_startup_checks(settings: Settings, recorder: AudioRecorder) -> None:
    errors: list[str] = []

    whisper_cli = settings.resolve_path(settings.providers.stt.whisper_cli)
    model_path = settings.resolve_path(settings.providers.stt.model)
    if not whisper_cli.exists():
        errors.append(
            "whisper-cli binary not found. Build whisper.cpp (make) or update providers.stt.whisper_cli."
        )
    else:
        try:
            _check_whisper_cli_runtime(whisper_cli)
        except StartupCheckError as exc:
            errors.append(str(exc))
    if not model_path.exists():
        errors.append(
            "Whisper model not found. Download a ggml model and update providers.stt.model "
            "or set WHISPER_MODEL_PATH in .env."
        )

    try:
        _check_ollama_connectivity(settings.providers.llm.url)
    except StartupCheckError as exc:
        errors.append(str(exc))

    try:
        with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            importlib.import_module("kokoro")
    except ModuleNotFoundError:
        errors.append(
            "Kokoro package is not importable. Install Kokoro in your active venv."
        )

    try:
        recorder.check_microphone_access()
    except StartupCheckError as exc:
        errors.append(str(exc))

    if errors:
        joined = "\n- " + "\n- ".join(errors)
        raise StartupCheckError(
            "Startup checks failed. Resolve the following issues before running Ruby:" + joined
        )


def _build_tool_registry(
    settings: Settings,
    confirm_callback: Callable[[str], bool] | None,
) -> ToolRegistry:
    workspace_guard = WorkspaceGuard(settings.workspace_dir)
    permission_policy = RiskPermissionPolicy(
        settings.security,
        confirm_callback=confirm_callback,
    )
    registry = ToolRegistry(permission_policy=permission_policy)

    system_tools = SystemTools(settings.tools.allowed_apps)
    file_tools = FileTools(workspace_guard)
    shell_tools = ShellTools(CommandPolicy(shell_enabled=settings.security.shell_enabled))

    def enabled(tool_name: str) -> bool:
        return tool_name in settings.tools.enabled

    registry.register(
        ToolDefinition(
            name="get_time",
            description="Return the local current time.",
            args_schema={},
            risk_level="low",
            enabled=enabled("get_time"),
            handler=system_tools.get_time,
        )
    )
    registry.register(
        ToolDefinition(
            name="open_app",
            description="Open an approved application by name.",
            args_schema={"app": "string"},
            risk_level="medium",
            enabled=enabled("open_app"),
            handler=system_tools.open_app,
        )
    )
    registry.register(
        ToolDefinition(
            name="list_directory",
            description="List files/folders inside ruby_workspace.",
            args_schema={"path": "string"},
            risk_level="low",
            enabled=enabled("list_directory"),
            handler=file_tools.list_directory,
        )
    )
    registry.register(
        ToolDefinition(
            name="create_folder",
            description="Create a folder inside ruby_workspace.",
            args_schema={"path": "string"},
            risk_level="low",
            enabled=enabled("create_folder"),
            handler=file_tools.create_folder,
        )
    )
    registry.register(
        ToolDefinition(
            name="create_file",
            description="Create a text file inside ruby_workspace.",
            args_schema={"path": "string", "content": "string"},
            risk_level="low",
            enabled=enabled("create_file"),
            handler=file_tools.create_file,
        )
    )
    registry.register(
        ToolDefinition(
            name="run_command",
            description="Run shell command if shell is enabled (off by default).",
            args_schema={"command": "string"},
            risk_level="high",
            enabled=enabled("run_command") and settings.security.shell_enabled,
            handler=shell_tools.run_command,
        )
    )

    _ = build_search_provider()
    return registry


def build_app_context(
    config_path: Path | None = None,
    confirm_callback: Callable[[str], bool] | None = None,
) -> AppContext:
    config_path = config_path or DEFAULT_CONFIG_PATH
    settings = load_settings(config_path)
    _ensure_runtime_dirs(PROJECT_ROOT, settings)

    recorder = AudioRecorder(sample_rate=settings.audio.sample_rate)
    _run_startup_checks(settings, recorder)

    tool_registry = _build_tool_registry(settings, confirm_callback=confirm_callback)
    assistant = RubyAssistant(
        stt_provider=build_stt_provider(settings),
        llm_provider=build_llm_provider(settings),
        tts_provider=build_tts_provider(settings),
        tool_registry=tool_registry,
        responses_dir=PROJECT_ROOT / "responses",
        conversation_enabled=settings.conversation.enabled,
        conversation_max_turns=settings.conversation.max_turns,
    )

    context = AppContext(
        settings=settings,
        assistant=assistant,
        recorder=recorder,
        player=AudioPlayer(),
        wake_detector=WakeWordDetector(
            enabled=settings.audio.wake_word_enabled,
            threshold=settings.audio.wake_threshold,
            chunk_size=settings.audio.wake_chunk_size,
            sample_rate=settings.audio.sample_rate,
        ),
    )
    return context


def dump_settings_snapshot(settings: Settings) -> str:
    snapshot = {
        "assistant": {
            "name": settings.assistant.name,
            "mode": settings.assistant.mode,
        },
        "providers": {
            "stt": settings.providers.stt.provider,
            "llm": settings.providers.llm.provider,
            "tts": settings.providers.tts.provider,
        },
        "conversation": {
            "enabled": settings.conversation.enabled,
            "max_turns": settings.conversation.max_turns,
        },
        "debug": settings.debug,
        "workspace_dir": str(settings.workspace_dir),
        "shell_enabled": settings.security.shell_enabled,
    }
    return json.dumps(snapshot, indent=2)
