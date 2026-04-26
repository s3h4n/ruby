"""Assistant entrypoint APIs shared by interfaces."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import datetime
import json
from pathlib import Path
import re
import threading

from ruby.core.conversation import ConversationManager
from ruby.core.errors import RubyError
from ruby.core.markdown_speech import markdown_to_speech_text
from ruby.core.pipeline import (
    AssistantPipeline,
    build_system_prompt,
    build_voice_system_prompt,
)
from ruby.core.schemas import AssistantResponse
from ruby.providers.llm.base import LLMProvider
from ruby.providers.stt.base import STTProvider
from ruby.providers.tts.base import TTSProvider
from ruby.tools.registry import ToolRegistry


_ACK_FALLBACK = "Okay, working on that."
_ACK_MAX_WORDS = 14


class RubyAssistant:
    """Reusable assistant core with text/audio handlers."""

    def __init__(
        self,
        stt_provider: STTProvider,
        llm_provider: LLMProvider,
        tts_provider: TTSProvider,
        tool_registry: ToolRegistry,
        responses_dir: Path,
        *,
        conversation_enabled: bool = True,
        conversation_max_turns: int = 6,
    ) -> None:
        self.stt_provider = stt_provider
        self.llm_provider = llm_provider
        self.tts_provider = tts_provider
        self.tool_registry = tool_registry
        self.pipeline = AssistantPipeline(tool_registry=tool_registry)
        self.system_prompt = build_system_prompt(tool_registry=tool_registry)
        self.voice_system_prompt = build_voice_system_prompt(tool_registry=tool_registry)
        self.responses_dir = responses_dir
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self.conversation = ConversationManager(
            enabled=conversation_enabled,
            max_turns=conversation_max_turns,
        )
        self._last_acknowledgement: str | None = None

    def handle_text(self, user_text: str) -> AssistantResponse:
        cleaned = user_text.strip()
        if not cleaned:
            return AssistantResponse(type="answer", text="I did not hear anything to process.")

        blocked_reason = _blocked_request_reason(cleaned)
        if blocked_reason:
            refusal = (
                "I can't help with that in v1. "
                f"Reason: {blocked_reason}. "
                "I can only run safe local tools."
            )
            self.conversation.add_user_message(cleaned)
            self.conversation.add_assistant_message(refusal)
            audio_path, warning = self._safe_synthesize(refusal)
            return AssistantResponse(
                type="answer",
                text=refusal,
                transcript=cleaned,
                audio_path=audio_path,
                warning=warning,
            )

        messages = self.conversation.get_messages(self.system_prompt, cleaned)
        llm_output = self.llm_provider.chat(messages)
        structured = self.pipeline.process_llm_output(llm_output)
        routed_type, response_text, tool_result = self.pipeline.route(structured)
        self.conversation.add_user_message(cleaned)
        self.conversation.add_assistant_message(response_text)
        audio_path, warning = self._safe_synthesize(response_text)
        return AssistantResponse(
            type=routed_type,
            text=response_text,
            transcript=cleaned,
            tool_name=structured.tool,
            tool_result=tool_result,
            audio_path=audio_path,
            warning=warning,
        )

    def handle_audio(self, audio_path: Path) -> AssistantResponse:
        transcript = self.stt_provider.transcribe(audio_path)
        result = self.handle_text(transcript)
        result.transcript = transcript
        return result

    def get_conversation_history(self) -> list[dict[str, str]]:
        return self.conversation.get_history()

    def clear_conversation(self) -> None:
        self.conversation.clear()

    def should_acknowledge_for_voice(self, user_text: str) -> bool:
        cleaned = user_text.strip().lower()
        if not cleaned:
            return False
        if len(cleaned.split()) >= 12:
            return True

        long_task_hints = (
            "create",
            "write",
            "draft",
            "generate",
            "build",
            "search",
            "find",
            "analyze",
            "summarize",
            "plan",
            "open",
            "run",
            "fix",
            "update",
            "refactor",
        )
        return any(hint in cleaned for hint in long_task_hints)

    def acknowledgement_for_voice(self, user_text: str) -> str:
        cleaned_user_text = user_text.strip()
        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "You generate quick spoken acknowledgements before longer tasks. "
                    "Return a single short sentence only (5-14 words), plain text, no lists."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Create a brief acknowledgement for this request before the assistant starts working: "
                    f"{cleaned_user_text}"
                ),
            },
        ]

        raw_phrase = ""
        try:
            raw_phrase = self.llm_provider.chat(prompt_messages)
        except RubyError:
            raw_phrase = ""

        phrase = self._normalize_acknowledgement(raw_phrase)
        if not phrase:
            phrase = _ACK_FALLBACK

        if self._last_acknowledgement is not None and phrase.lower() == self._last_acknowledgement.lower():
            phrase = f"{phrase.rstrip('.')} now."

        self._last_acknowledgement = phrase
        return phrase

    @staticmethod
    def _normalize_acknowledgement(raw_text: str) -> str:
        candidate = raw_text.strip()
        if not candidate:
            return ""

        if candidate.startswith("{"):
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                maybe_text = payload.get("text") or payload.get("content")
                if isinstance(maybe_text, str):
                    candidate = maybe_text.strip()

        candidate = markdown_to_speech_text(candidate)
        candidate = re.sub(r"\s+", " ", candidate).strip().strip('"')
        if not candidate:
            return ""

        first_line = candidate.splitlines()[0].strip()
        sentence_match = re.search(r"[.!?]", first_line)
        if sentence_match is not None:
            first_line = first_line[: sentence_match.end()]

        words = first_line.split()
        if len(words) > _ACK_MAX_WORDS:
            first_line = " ".join(words[:_ACK_MAX_WORDS]).rstrip(".,!?") + "."

        if not first_line.endswith((".", "!", "?")):
            first_line = first_line.rstrip(".,!?") + "."

        return first_line

    def stream_voice_response(
        self,
        user_text: str,
        *,
        cancel_event: threading.Event | None = None,
        on_first_token: Callable[[float], None] | None = None,
    ) -> Iterator[str]:
        cleaned = user_text.strip()
        if not cleaned:
            return

        blocked_reason = _blocked_request_reason(cleaned)
        if blocked_reason:
            refusal = (
                "I can't help with that in v1. "
                f"Reason: {blocked_reason}. "
                "I can only run safe local tools."
            )
            yield refusal
            return

        messages = self.conversation.get_messages(self.voice_system_prompt, cleaned)
        yield from self.llm_provider.stream_chat(
            messages,
            on_first_token=on_first_token,
            cancel_event=cancel_event,
        )

    def finalize_voice_turn(
        self,
        transcript: str,
        final_text: str,
        *,
        interrupted: bool,
    ) -> AssistantResponse:
        cleaned = transcript.strip()
        response_text = final_text.strip() or "I am ready."
        if cleaned:
            self.conversation.add_user_message(cleaned)
        if not interrupted and response_text:
            self.conversation.add_assistant_message(response_text)
        return AssistantResponse(
            type="answer",
            text=response_text,
            transcript=cleaned,
        )

    def _synthesize(self, text: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = self.responses_dir / f"response-{stamp}.wav"
        return self.tts_provider.synthesize(text, output_path)

    def _safe_synthesize(self, text: str) -> tuple[str, str]:
        try:
            audio_path = self._synthesize(markdown_to_speech_text(text))
            return str(audio_path), ""
        except RubyError:
            return "", "Text response generated, but speech failed."


def _blocked_request_reason(user_text: str) -> str:
    lowered = user_text.lower()
    blocked_fragments = {
        "rm -rf": "destructive shell command",
        "sudo": "privileged command",
        "chmod": "system modification command",
        "chown": "system ownership change",
        "diskutil": "disk/system utility command",
        "delete system": "system modification attempt",
        "format disk": "destructive system request",
    }
    for fragment, reason in blocked_fragments.items():
        if fragment in lowered:
            return reason
    return ""
