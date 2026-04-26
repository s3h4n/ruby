from __future__ import annotations

from pathlib import Path

import pytest

from ruby.core.errors import SafetyError
from ruby.core.schemas import ToolDefinition
from ruby.security.paths import safe_resolve_workspace_path
from ruby.tools.registry import ToolRegistry


class _AllowAllPolicy:
    def allow(self, risk_level: str, action_name: str) -> bool:
        del risk_level, action_name
        return True


def test_safe_resolve_workspace_path_blocks_traversal(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "ruby_workspace"
    workspace_dir.mkdir()

    with pytest.raises(SafetyError):
        safe_resolve_workspace_path(workspace_dir, "../outside.txt")


def test_safe_resolve_workspace_path_blocks_absolute_outside_workspace(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "ruby_workspace"
    workspace_dir.mkdir()

    with pytest.raises(SafetyError):
        safe_resolve_workspace_path(workspace_dir, "/tmp/notes.txt")


def test_safe_resolve_workspace_path_allows_workspace_relative_paths(tmp_path: Path) -> None:
    workspace_dir = tmp_path / "ruby_workspace"
    workspace_dir.mkdir()

    resolved = safe_resolve_workspace_path(workspace_dir, "notes/today.txt")
    assert resolved == (workspace_dir / "notes" / "today.txt").resolve()


def test_registry_rejects_unknown_tool() -> None:
    registry = ToolRegistry(permission_policy=_AllowAllPolicy())

    result = registry.execute("missing_tool", {})
    assert result.success is False
    assert "Unsupported tool" in result.message


def test_registry_executes_enabled_tool() -> None:
    registry = ToolRegistry(permission_policy=_AllowAllPolicy())
    registry.register(
        ToolDefinition(
            name="hello",
            description="hello tool",
            args_schema={},
            risk_level="low",
            enabled=True,
            handler=lambda _: "hello world",
        )
    )

    result = registry.execute("hello", {})
    assert result.success is True
    assert result.message == "hello world"
