from __future__ import annotations

from pathlib import Path

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
