from __future__ import annotations

from pathlib import Path
import threading

from ruby.core.assistant import RubyAssistant
from ruby.providers.llm.base import LLMProvider
from ruby.providers.stt.base import STTProvider
from ruby.providers.tts.base import TTSProvider


class _FakeLLM(LLMProvider):
    def __init__(self, output: str) -> None:
        self._output = output

    def chat(self, messages: list[dict[str, str]]) -> str:
        _ = messages
        return self._output


class _CapturingVoiceLLM(LLMProvider):
    def __init__(self) -> None:
        self.messages_seen: list[dict[str, str]] = []

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.messages_seen = messages
        return '{"type":"answer","text":"unused"}'

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        on_first_token=None,
        cancel_event: threading.Event | None = None,
    ):
        _ = cancel_event
        self.messages_seen = messages
        if on_first_token is not None:
            on_first_token(1.0)
        yield "Hello"


class _AckCapturingLLM(LLMProvider):
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.messages_seen: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]]) -> str:
        self.messages_seen.append(messages)
        if not self._responses:
            return "Okay, working on that."
        return self._responses.pop(0)


class _FakeSTT(STTProvider):
    def transcribe(self, audio_path: Path) -> str:
        _ = audio_path
        return ""


class _CaptureTTS(TTSProvider):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def synthesize(self, text: str, output_path: Path) -> Path:
        self.calls.append(text)
        return output_path


class _NoopRegistry:
    def describe_enabled_tools(self) -> str:
        return ""


def test_assistant_keeps_markdown_visible_but_speaks_normalized_text(tmp_path: Path) -> None:
    markdown_answer = '{"type":"answer","text":"# Title\\nUse **bold** and [Ruby docs](https://example.com)."}'
    tts = _CaptureTTS()
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=_FakeLLM(markdown_answer),
        tts_provider=tts,
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    response = assistant.handle_text("hello")

    assert response.text == "# Title\nUse **bold** and [Ruby docs](https://example.com)."
    assert tts.calls
    spoken = tts.calls[-1]
    assert "#" not in spoken
    assert "**" not in spoken
    assert "[" not in spoken
    assert "Title" in spoken
    assert "Ruby docs" in spoken


def test_assistant_preserves_plain_text_for_tts(tmp_path: Path) -> None:
    plain_answer = '{"type":"answer","text":"Hello from Ruby."}'
    tts = _CaptureTTS()
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=_FakeLLM(plain_answer),
        tts_provider=tts,
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    response = assistant.handle_text("hello")

    assert response.text == "Hello from Ruby."
    assert tts.calls[-1] == "Hello from Ruby."


def test_voice_acknowledgement_heuristic_prefers_short_direct_answers(tmp_path: Path) -> None:
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=_FakeLLM('{"type":"answer","text":"ok"}'),
        tts_provider=_CaptureTTS(),
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    assert assistant.should_acknowledge_for_voice("What time is it?") is False
    assert assistant.should_acknowledge_for_voice("Please search the workspace and summarize pending tasks") is True


def test_voice_acknowledgement_is_generated_by_llm(tmp_path: Path) -> None:
    llm = _AckCapturingLLM(["Absolutely, give me a second while I work on that."])
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=llm,
        tts_provider=_CaptureTTS(),
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    phrase = assistant.acknowledgement_for_voice("Please draft a long project update")

    assert "give me a second" in phrase.lower()
    assert llm.messages_seen
    assert "acknowledgement" in llm.messages_seen[0][0]["content"].lower()
    assert "please draft a long project update" in llm.messages_seen[0][1]["content"].lower()


def test_voice_acknowledgement_avoids_adjacent_repetition(tmp_path: Path) -> None:
    llm = _AckCapturingLLM(
        [
            "Okay, working on that.",
            "Okay, working on that.",
        ]
    )
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=llm,
        tts_provider=_CaptureTTS(),
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    first = assistant.acknowledgement_for_voice("Can you summarize this")
    second = assistant.acknowledgement_for_voice("Can you summarize this again")

    assert first != second


def test_finalize_voice_turn_skips_assistant_message_on_interrupt(tmp_path: Path) -> None:
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=_FakeLLM('{"type":"answer","text":"ok"}'),
        tts_provider=_CaptureTTS(),
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    assistant.finalize_voice_turn(
        transcript="user turn",
        final_text="partial response",
        interrupted=True,
    )
    history = assistant.get_conversation_history()

    assert history == [{"role": "user", "content": "user turn"}]


def test_stream_voice_response_uses_voice_system_prompt(tmp_path: Path) -> None:
    llm = _CapturingVoiceLLM()
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=llm,
        tts_provider=_CaptureTTS(),
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    chunks = list(assistant.stream_voice_response("tell me a joke"))

    assert chunks == ["Hello"]
    assert llm.messages_seen
    assert llm.messages_seen[0]["role"] == "system"
    assert llm.messages_seen[0]["content"] == assistant.voice_system_prompt


def test_voice_system_prompt_requires_short_plain_paragraph_responses(tmp_path: Path) -> None:
    assistant = RubyAssistant(
        stt_provider=_FakeSTT(),
        llm_provider=_FakeLLM('{"type":"answer","text":"ok"}'),
        tts_provider=_CaptureTTS(),
        tool_registry=_NoopRegistry(),
        responses_dir=tmp_path,
    )

    prompt = assistant.voice_system_prompt.lower()

    assert "no more than 4 sentences" in prompt
    assert "single paragraph" in prompt
    assert "no tables" in prompt
    assert "no bullet points" in prompt
