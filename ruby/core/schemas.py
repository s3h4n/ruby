"""Typed schemas shared across assistant modules."""

from __future__ import annotations

from dataclasses import field
from typing import Any, Callable, Literal

from ruby.core.compat import compat_dataclass


RiskLevel = Literal["low", "medium", "high"]
ResponseType = Literal["answer", "tool_call", "intent"]


@compat_dataclass(slots=True)
class LLMStructuredResponse:
    """Normalized structured response returned by the LLM."""

    type: ResponseType
    text: str = ""
    tool: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    intent: str = ""


@compat_dataclass(slots=True)
class AssistantResponse:
    """Final response returned by assistant entrypoints."""

    type: ResponseType
    text: str
    transcript: str = ""
    tool_name: str = ""
    tool_result: str = ""
    audio_path: str = ""
    warning: str = ""


@compat_dataclass(slots=True)
class ToolDefinition:
    """Tool metadata and runtime handler."""

    name: str
    description: str
    args_schema: dict[str, str]
    risk_level: RiskLevel
    enabled: bool
    handler: Callable[[dict[str, Any]], str]


@compat_dataclass(slots=True)
class ToolResult:
    """Outcome of a tool call routed through the registry."""

    success: bool
    message: str
    tool_name: str = ""


# Backward-compatible alias for older imports.
ToolExecutionResult = ToolResult
