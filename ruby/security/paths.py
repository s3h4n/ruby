"""Workspace path sandbox helpers."""

from __future__ import annotations

from pathlib import Path

from ruby.core.errors import SafetyError


def safe_resolve_workspace_path(workspace_dir: Path, requested_path: str) -> Path:
    workspace_root = workspace_dir.expanduser().resolve()
    requested_raw = requested_path.strip()
    if requested_raw.startswith("~"):
        raise SafetyError("Home-expansion paths are not allowed in workspace operations.")

    requested = Path(requested_raw or ".")
    if ".." in requested.parts:
        raise SafetyError("Path traversal blocked. Access outside ruby_workspace is not allowed.")

    if requested.is_absolute():
        candidate = requested.resolve()
    else:
        candidate = (workspace_root / requested).resolve()

    if workspace_root not in candidate.parents and candidate != workspace_root:
        raise SafetyError("Path traversal blocked. Access outside ruby_workspace is not allowed.")

    relative_parts = candidate.relative_to(workspace_root).parts
    for part in relative_parts:
        if part.startswith("."):
            raise SafetyError("Hidden paths are not allowed in v1 workspace operations.")

    return candidate
