"""Ollama local API provider implementation."""

from __future__ import annotations

from collections.abc import Callable, Iterator
import json
import threading
import time
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

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        on_first_token: Callable[[float], None] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Iterator[str]:
        payload = {
            "model": self.model,
            "stream": True,
            "messages": messages,
        }
        request = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        started_at = time.monotonic()
        first_token_reported = False
        saw_content = False

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                for raw_line in response:
                    if cancel_event is not None and cancel_event.is_set():
                        return

                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue

                    try:
                        parsed = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ProviderError(
                            f"Invalid Ollama JSON stream chunk: {line[:300]}"
                        ) from exc

                    message = parsed.get("message", {})
                    content = str(message.get("content", ""))
                    if content:
                        if not first_token_reported and on_first_token is not None:
                            on_first_token((time.monotonic() - started_at) * 1000.0)
                            first_token_reported = True
                        saw_content = True
                        yield content

                    if parsed.get("done"):
                        break
        except urllib.error.URLError as exc:
            raise ProviderError("Could not reach Ollama. Is Ollama running?") from exc

        if not saw_content and not (cancel_event is not None and cancel_event.is_set()):
            raise ProviderError("Ollama returned an empty streamed message.")
