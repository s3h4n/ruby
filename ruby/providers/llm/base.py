"""LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
import threading


class LLMProvider(ABC):
    """Language-model provider contract."""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        """Return the raw assistant response string."""

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        *,
        on_first_token: Callable[[float], None] | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Iterator[str]:
        """Yield response chunks for providers that support streaming.

        Providers without native streaming support fall back to a single full message.
        `on_first_token` receives latency in milliseconds measured by the provider.
        """
        del cancel_event
        response = self.chat(messages)
        if response:
            if on_first_token is not None:
                on_first_token(0.0)
            yield response
