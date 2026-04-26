"""LLM provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Language-model provider contract."""

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        """Return the raw assistant response string."""
