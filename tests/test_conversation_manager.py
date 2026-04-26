from __future__ import annotations

from ruby.core.conversation import ConversationManager


def test_conversation_manager_trims_to_max_turns() -> None:
    manager = ConversationManager(enabled=True, max_turns=2)

    manager.add_user_message("turn1-user")
    manager.add_assistant_message("turn1-assistant")
    manager.add_user_message("turn2-user")
    manager.add_assistant_message("turn2-assistant")
    manager.add_user_message("turn3-user")
    manager.add_assistant_message("turn3-assistant")

    history = manager.get_history()
    assert len(history) == 4
    assert history[0]["content"] == "turn2-user"
    assert history[-1]["content"] == "turn3-assistant"


def test_get_messages_includes_system_history_and_latest_user() -> None:
    manager = ConversationManager(enabled=True, max_turns=3)
    manager.add_user_message("previous-question")
    manager.add_assistant_message("previous-answer")

    messages = manager.get_messages("system-prompt", "latest-question")

    assert messages[0] == {"role": "system", "content": "system-prompt"}
    assert messages[1] == {"role": "user", "content": "previous-question"}
    assert messages[2] == {"role": "assistant", "content": "previous-answer"}
    assert messages[3] == {"role": "user", "content": "latest-question"}


def test_disabled_conversation_only_sends_system_and_current_user() -> None:
    manager = ConversationManager(enabled=False, max_turns=3)
    manager.add_user_message("should-not-store")
    manager.add_assistant_message("should-not-store")

    messages = manager.get_messages("system-prompt", "latest-question")

    assert messages == [
        {"role": "system", "content": "system-prompt"},
        {"role": "user", "content": "latest-question"},
    ]
    assert manager.get_history() == []


def test_clear_resets_history() -> None:
    manager = ConversationManager(enabled=True, max_turns=3)
    manager.add_user_message("hello")
    manager.add_assistant_message("hi")

    manager.clear()

    assert manager.get_history() == []
