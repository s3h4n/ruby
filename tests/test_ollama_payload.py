from __future__ import annotations

import json

from ruby.providers.llm.ollama import OllamaLLMProvider


class _FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def read(self) -> bytes:
        return self._body


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
