"""Core text-processing pipeline and LLM response routing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ruby.core.errors import RubyError
from ruby.core.schemas import LLMStructuredResponse
from ruby.tools.registry import ToolRegistry


FALLBACK_UNSUPPORTED_INTENT = "That intent is not implemented yet."
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "system_prompt.md"
DEFAULT_VOICE_SYSTEM_PROMPT_PATH = PROJECT_ROOT / "prompts" / "voice_system_prompt.md"


def _extract_json_candidate(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[:-3]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return ""
    return text[start : end + 1]


def parse_llm_structured_response(raw_text: str) -> LLMStructuredResponse:
    candidate = _extract_json_candidate(raw_text)
    if not candidate:
        return LLMStructuredResponse(type="answer", text=raw_text.strip())

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return LLMStructuredResponse(type="answer", text=raw_text.strip())

    response_type = str(parsed.get("type", "answer")).strip()
    if response_type not in {"answer", "tool_call", "intent"}:
        return LLMStructuredResponse(type="answer", text=raw_text.strip())

    return LLMStructuredResponse(
        type=response_type,
        text=str(parsed.get("text", "")).strip(),
        tool=str(parsed.get("tool", "")).strip(),
        args=dict(parsed.get("args", {}) or {}),
        intent=str(parsed.get("intent", "")).strip(),
    )


def _load_system_prompt_template(prompt_path: Path) -> str:
    if not prompt_path.exists():
        raise RubyError(
            "Missing prompt resource file. "
            f"Expected {prompt_path.name} in prompts/system_prompt.md location "
            "(or configured prompt path for tests)."
        )
    try:
        template = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RubyError(
            "Could not read prompt resource file. Check prompts/system_prompt.md permissions."
        ) from exc
    if not template:
        raise RubyError("Prompt resource file is empty: prompts/system_prompt.md")
    return template


def build_system_prompt(
    tool_registry: ToolRegistry,
    *,
    prompt_path: Path | None = None,
) -> str:
    prompt_template = _load_system_prompt_template(prompt_path or DEFAULT_SYSTEM_PROMPT_PATH)
    tools_description = tool_registry.describe_enabled_tools() or "- No tools are enabled."
    return prompt_template.replace("{{enabled_tools}}", tools_description)


def build_voice_system_prompt(
    tool_registry: ToolRegistry,
    *,
    prompt_path: Path | None = None,
) -> str:
    prompt_template = _load_system_prompt_template(prompt_path or DEFAULT_VOICE_SYSTEM_PROMPT_PATH)
    tools_description = tool_registry.describe_enabled_tools() or "- No tools are enabled."
    return prompt_template.replace("{{enabled_tools}}", tools_description)


class AssistantPipeline:
    """Runs LLM output parsing and optional tool execution."""

    def __init__(self, tool_registry: ToolRegistry) -> None:
        self.tool_registry = tool_registry

    def process_llm_output(self, llm_output: str) -> LLMStructuredResponse:
        structured = parse_llm_structured_response(llm_output)
        if structured.type == "intent" and not structured.text:
            structured.text = FALLBACK_UNSUPPORTED_INTENT
        return structured

    def route(self, structured: LLMStructuredResponse) -> tuple[str, str, str]:
        """Return tuple: (type, response_text, tool_result)."""
        if structured.type == "answer":
            return "answer", structured.text or "I am ready.", ""

        if structured.type == "intent":
            return "intent", structured.text or FALLBACK_UNSUPPORTED_INTENT, ""

        if structured.type == "tool_call":
            result = self.tool_registry.execute(structured.tool, structured.args)
            if result.success:
                return "tool_call", result.message, result.message
            return "answer", f"I couldn't run that tool safely: {result.message}", result.message

        return "answer", "I could not understand the request.", ""
