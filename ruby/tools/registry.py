"""Tool registry and execution gateway."""

from __future__ import annotations

from typing import Any

from ruby.core.errors import ToolError
from ruby.core.schemas import ToolDefinition, ToolResult
from ruby.security.permissions import RiskPermissionPolicy


class ToolRegistry:
    """Central registry for safe tool execution."""

    def __init__(self, permission_policy: RiskPermissionPolicy) -> None:
        self._permission_policy = permission_policy
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.name in self._tools:
            raise ToolError(f"Tool '{definition.name}' is already registered.")
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list_enabled(self) -> list[ToolDefinition]:
        return [tool for tool in self._tools.values() if tool.enabled]

    def describe_enabled_tools(self) -> str:
        lines: list[str] = []
        for tool in sorted(self.list_enabled(), key=lambda item: item.name):
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def execute(self, name: str, args: dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                message=f"Unsupported tool: {name}",
                tool_name=name,
            )
        if not tool.enabled:
            return ToolResult(
                success=False,
                message=f"Tool '{name}' is disabled.",
                tool_name=name,
            )
        if not self._permission_policy.allow(tool.risk_level, name):
            return ToolResult(
                success=False,
                message=f"Tool '{name}' blocked by risk policy.",
                tool_name=name,
            )

        try:
            result_message = tool.handler(args)
        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                success=False,
                message=f"Tool '{name}' failed: {exc}",
                tool_name=name,
            )

        return ToolResult(success=True, message=result_message, tool_name=name)
