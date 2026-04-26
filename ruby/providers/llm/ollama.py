"""Ollama local API provider implementation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ruby.core.errors import ProviderError
from ruby.providers.llm.base import LLMProvider


class OllamaLLMProvider(LLMProvider):
    """Chat provider that uses Ollama's local HTTP API."""

    def __init__(self, model: str, url: str, timeout_seconds: int = 120) -> None:
        self.model = model
        self.url = url
        self.timeout_seconds = timeout_seconds

    def chat(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": messages,
        }
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.URLError as exc:
            raise ProviderError("Could not reach Ollama. Is Ollama running?") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError(f"Invalid Ollama JSON response: {body[:300]}") from exc

        message = parsed.get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise ProviderError("Ollama returned an empty message.")
        return content
