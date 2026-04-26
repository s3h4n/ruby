"""OpenRouter LLM provider placeholder (disabled by default)."""

from __future__ import annotations

from collections.abc import Callable, Iterator
import json
import os
import threading
import time

from ruby.core.errors import ProviderError
from ruby.providers.llm.base import LLMProvider


class OpenRouterLLMProvider(LLMProvider):
    """Provider implementation for OpenRouter HTTP API."""

    def __init__(self, model: str, timeout_seconds: int = 60) -> None:
        self.model = model
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _api_key() -> str:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise ProviderError(
                "OPENROUTER_API_KEY is missing. Set it in .env before using OpenRouter provider."
            )
        return api_key

    def chat(self, messages: list[dict[str, str]]) -> str:
        api_key = self._api_key()

        try:
            import requests
        except ModuleNotFoundError as exc:
            raise ProviderError("Missing dependency 'requests'. Install project dependencies.") from exc

        payload = {
            "model": self.model,
            "messages": messages,
        }
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"OpenRouter request failed: {exc}") from exc

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ProviderError("OpenRouter returned no choices.")

        message = choices[0].get("message", {})
        content = str(message.get("content", "")).strip()
        if not content:
            raise ProviderError("OpenRouter returned empty content.")
        return content

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        on_first_token: Callable[[float], None] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Iterator[str]:
        api_key = self._api_key()

        try:
            import requests
        except ModuleNotFoundError as exc:
            raise ProviderError("Missing dependency 'requests'. Install project dependencies.") from exc

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
        }

        started_at = time.monotonic()
        first_token_reported = False
        saw_content = False

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
                stream=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"OpenRouter request failed: {exc}") from exc

        for line in response.iter_lines(decode_unicode=True):
            if cancel_event is not None and cancel_event.is_set():
                return
            if not line:
                continue
            stripped = line.strip()
            if not stripped.startswith("data:"):
                continue
            payload_str = stripped[5:].strip()
            if not payload_str or payload_str == "[DONE]":
                break

            try:
                parsed = json.loads(payload_str)
            except json.JSONDecodeError as exc:
                raise ProviderError(
                    f"Invalid OpenRouter JSON stream chunk: {payload_str[:300]}"
                ) from exc

            choices = parsed.get("choices", [])
            if not choices:
                continue
            choice = choices[0]
            delta = choice.get("delta", {})
            content = str(delta.get("content", ""))
            if not content:
                message = choice.get("message", {})
                content = str(message.get("content", ""))

            if content:
                if not first_token_reported and on_first_token is not None:
                    on_first_token((time.monotonic() - started_at) * 1000.0)
                    first_token_reported = True
                saw_content = True
                yield content

        if not saw_content and not (cancel_event is not None and cancel_event.is_set()):
            raise ProviderError("OpenRouter returned an empty streamed message.")
