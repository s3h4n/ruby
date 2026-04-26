from __future__ import annotations

from ruby.providers.llm.openrouter import OpenRouterLLMProvider


class _FakeStreamResponse:
    def __init__(self, chunks: list[str]) -> None:
        self._chunks = chunks

    def raise_for_status(self) -> None:
        return None

    def iter_lines(self, decode_unicode: bool = False):
        del decode_unicode
        for chunk in self._chunks:
            yield chunk


def test_openrouter_stream_chat_requests_streaming_and_yields_chunks(monkeypatch) -> None:
    provider = OpenRouterLLMProvider(model="openai/gpt-4o-mini")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    captured: dict[str, object] = {}
    stream_lines = [
        'data: {"choices":[{"delta":{"content":"Hello"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        "data: [DONE]",
    ]

    def fake_post(url, headers, json, timeout, stream=False):  # noqa: ANN001
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        captured["stream"] = stream
        return _FakeStreamResponse(stream_lines)

    import requests

    monkeypatch.setattr(requests, "post", fake_post)

    chunks = list(provider.stream_chat([{"role": "user", "content": "hi"}]))

    assert "".join(chunks) == "Hello world"
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["stream"] is True
    assert captured["json"] == {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": True,
    }
