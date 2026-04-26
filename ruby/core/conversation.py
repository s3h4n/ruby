"""Conversation history manager for in-session context."""

from __future__ import annotations

from copy import deepcopy


class ConversationManager:
    """Maintains bounded user/assistant history for a single session."""

    def __init__(self, enabled: bool = True, max_turns: int = 6) -> None:
        self.enabled = enabled
        self.max_turns = max_turns
        self._history: list[dict[str, str]] = []

    def add_user_message(self, text: str) -> None:
        if not self.enabled:
            return
        cleaned = text.strip()
        if not cleaned:
            return
        self._history.append({"role": "user", "content": cleaned})
        self._trim_turns()

    def add_assistant_message(self, text: str) -> None:
        if not self.enabled:
            return
        cleaned = text.strip()
        if not cleaned:
            return
        self._history.append({"role": "assistant", "content": cleaned})
        self._trim_turns()

    def get_messages(self, system_prompt: str, user_message: str | None = None) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        if self.enabled:
            messages.extend(deepcopy(self._history))

        if user_message is not None:
            cleaned = user_message.strip()
            if cleaned:
                messages.append({"role": "user", "content": cleaned})
        return messages

    def clear(self) -> None:
        self._history.clear()

    def get_history(self) -> list[dict[str, str]]:
        return deepcopy(self._history)

    def _trim_turns(self) -> None:
        if not self.enabled:
            self._history.clear()
            return

        max_messages = self.max_turns * 2
        if len(self._history) <= max_messages:
            return
        self._history = self._history[-max_messages:]
