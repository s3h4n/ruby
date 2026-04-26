from __future__ import annotations

from collections.abc import Iterator
import json
import threading

from ruby.providers.llm.base import LLMProvider
from ruby.providers.llm.ollama import OllamaLLMProvider


class _FakeResponse:
    def __init__(self, body: str, lines: list[str] | None = None) -> None:
        self._body = body.encode("utf-8")
        self._lines = [line.encode("utf-8") for line in (lines or [])]

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def read(self) -> bytes:
        return self._body

    def __iter__(self) -> Iterator[bytes]:
        return iter(self._lines)


def test_ollama_provider_sends_role_based_history_with_stream_false(monkeypatch) -> None:
    provider = OllamaLLMProvider(model="gemma4:e2b", url="http://localhost:11434/api/chat")
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout):  # noqa: ANN001
        del timeout
        payload = json.loads(request.data.decode("utf-8"))
        captured["payload"] = payload
        return _FakeResponse('{"message": {"content": "ok"}}')

    monkeypatch.setattr("ruby.providers.llm.ollama.urllib.request.urlopen", fake_urlopen)

    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "first-answer"},
        {"role": "user", "content": "follow-up"},
    ]
    reply = provider.chat(messages)

    assert reply == "ok"
    assert captured["payload"] == {
        "model": "gemma4:e2b",
        "stream": False,
        "messages": messages,
    }


def test_ollama_provider_stream_chat_yields_chunks_and_stream_true(monkeypatch) -> None:
    provider = OllamaLLMProvider(model="gemma4:e2b", url="http://localhost:11434/api/chat")
    captured: dict[str, object] = {}

    lines = [
        '{"message": {"content": "Hello"}, "done": false}',
        '{"message": {"content": " there"}, "done": false}',
        '{"done": true}',
    ]

    def fake_urlopen(request, timeout):  # noqa: ANN001
        del timeout
        payload = json.loads(request.data.decode("utf-8"))
        captured["payload"] = payload
        return _FakeResponse("", lines=lines)

    monkeypatch.setattr("ruby.providers.llm.ollama.urllib.request.urlopen", fake_urlopen)

    chunks = list(provider.stream_chat([{"role": "user", "content": "hi"}]))

    assert "".join(chunks) == "Hello there"
    assert captured["payload"] == {
        "model": "gemma4:e2b",
        "stream": True,
        "messages": [{"role": "user", "content": "hi"}],
    }


def test_llm_base_stream_falls_back_to_chat_and_reports_first_token() -> None:
    class _BasicProvider(LLMProvider):
        def chat(self, messages: list[dict[str, str]]) -> str:
            _ = messages
            return "done"

    provider = _BasicProvider()
    first_token_ms: list[float] = []
    chunks = list(
        provider.stream_chat(
            [{"role": "user", "content": "hello"}],
            on_first_token=first_token_ms.append,
            cancel_event=threading.Event(),
        )
    )

    assert chunks == ["done"]
    assert first_token_ms == [0.0]
