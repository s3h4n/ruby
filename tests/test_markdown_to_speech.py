from __future__ import annotations

from ruby.core.markdown_speech import markdown_to_speech_text


def test_headings_are_spoken_without_hash_markers() -> None:
    spoken = markdown_to_speech_text("# Title\n## Subtitle")
    assert "#" not in spoken
    assert "Title" in spoken
    assert "Subtitle" in spoken


def test_bold_and_italic_markers_are_removed() -> None:
    spoken = markdown_to_speech_text("Use **bold** and _italic_ text.")
    assert "**" not in spoken
    assert "_" not in spoken
    assert "bold" in spoken
    assert "italic" in spoken


def test_inline_code_and_code_fences_are_normalized() -> None:
    spoken = markdown_to_speech_text("Use `print()`\n```python\nprint('ok')\n```")
    assert "`" not in spoken
    assert "print()" in spoken
    assert "print('ok')" in spoken


def test_links_prefer_human_readable_label() -> None:
    spoken = markdown_to_speech_text("Read [Ruby docs](https://example.com/docs).")
    assert "[" not in spoken
    assert "](" not in spoken
    assert "Ruby docs" in spoken


def test_bullet_and_numbered_lists_become_readable_sequences() -> None:
    spoken = markdown_to_speech_text("- first\n- second\n1. one\n2. two")
    assert "- " not in spoken
    assert "first" in spoken
    assert "second" in spoken
    assert "one" in spoken
    assert "two" in spoken


def test_tables_do_not_speak_pipes_or_separator_rows() -> None:
    spoken = markdown_to_speech_text(
        "| name | value |\n| --- | --- |\n| model | gemma |\n| mode | voice |"
    )
    assert "|" not in spoken
    assert "---" not in spoken
    assert "model" in spoken
    assert "gemma" in spoken


def test_plain_text_is_preserved_without_unnecessary_changes() -> None:
    text = "Ruby is running locally."
    assert markdown_to_speech_text(text) == text


def test_mixed_markdown_is_handled_in_single_pass() -> None:
    spoken = markdown_to_speech_text(
        "# Plan\n- Visit [docs](https://example.com)\n- Run `python app.py run`"
    )
    assert "#" not in spoken
    assert "[" not in spoken
    assert "`" not in spoken
    assert "Plan" in spoken
    assert "docs" in spoken
    assert "python app.py run" in spoken


def test_symbol_heavy_text_is_normalized_for_tts() -> None:
    spoken = markdown_to_speech_text(
        "Move -> Jump -> attack. Try queue_entry() and 2 + 2 = 4; use [fast_mode] and a\\b."
    )

    assert "->" not in spoken
    assert "_" not in spoken
    assert "(" not in spoken
    assert ")" not in spoken
    assert "[" not in spoken
    assert "]" not in spoken
    assert "\\" not in spoken
    assert "plus" in spoken
    assert "equals" in spoken
    assert "then" in spoken
