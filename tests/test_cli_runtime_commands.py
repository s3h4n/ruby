from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from ruby.interfaces import cli


def _build_context() -> SimpleNamespace:
    assistant = Mock()
    assistant.get_conversation_history.return_value = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]

    settings = SimpleNamespace(
        assistant=SimpleNamespace(name="Ruby"),
        providers=SimpleNamespace(
            stt=SimpleNamespace(provider="whisper_cpp", model="stt-model.bin", whisper_cli="/tmp/whisper-cli"),
            llm=SimpleNamespace(provider="ollama", model="gemma4:e2b", url="http://localhost:11434/api/chat"),
            tts=SimpleNamespace(provider="kokoro", voice="af_bella"),
        ),
        conversation=SimpleNamespace(enabled=True, max_turns=6),
        debug=False,
    )

    return SimpleNamespace(
        settings=settings,
        assistant=assistant,
        recorder=Mock(),
        player=Mock(),
    )


def test_slash_commands_are_handled_locally_without_llm_calls(monkeypatch) -> None:
    context = _build_context()
    context.assistant.handle_text.side_effect = AssertionError("LLM path should not be called")

    responses = iter(["/help", "/status", "/history", "/clear", "/quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))

    result = cli._interactive_loop(context)

    assert result == 0
    context.assistant.handle_text.assert_not_called()
    context.assistant.clear_conversation.assert_called_once()


def test_unknown_runtime_command_does_not_exit() -> None:
    context = _build_context()

    should_exit = cli._handle_runtime_command(context, "/not-a-command")

    assert should_exit is False
    context.assistant.handle_text.assert_not_called()
