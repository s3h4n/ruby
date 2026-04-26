"""Workspace-scoped file tools for v1."""

from __future__ import annotations

from pathlib import Path

from ruby.security.permissions import WorkspaceGuard


class FileTools:
    """Safe file operations restricted to ruby_workspace."""

    def __init__(self, workspace_guard: WorkspaceGuard) -> None:
        self.workspace_guard = workspace_guard

    def list_directory(self, args: dict[str, object]) -> str:
        relative_path = str(args.get("path", "."))
        target = self.workspace_guard.safe_path(relative_path)
        if not target.exists():
            return f"Path does not exist in workspace: {relative_path}"
        if not target.is_dir():
            return f"Path is not a directory: {relative_path}"

        entries = sorted(target.iterdir(), key=lambda item: item.name.lower())
        if not entries:
            return "Workspace directory is empty."
        lines = []
        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            lines.append(f"{entry.name}{suffix}")
        return "\n".join(lines)

    def create_folder(self, args: dict[str, object]) -> str:
        relative_path = str(args.get("path", "")).strip()
        if not relative_path:
            return "Missing 'path' argument for create_folder."

        target = self.workspace_guard.safe_path(relative_path)
        target.mkdir(parents=True, exist_ok=True)
        return f"Created folder: {target.relative_to(self.workspace_guard.workspace_dir)}"

    def create_file(self, args: dict[str, object]) -> str:
        relative_path = str(args.get("path", "")).strip()
        content = str(args.get("content", ""))
        if not relative_path:
            return "Missing 'path' argument for create_file."

        target = self.workspace_guard.safe_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Created file: {target.relative_to(self.workspace_guard.workspace_dir)}"
