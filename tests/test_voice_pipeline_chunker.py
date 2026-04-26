from __future__ import annotations

from ruby.core.voice_pipeline import SpeechChunker


def test_chunker_emits_on_sentence_punctuation() -> None:
    chunker = SpeechChunker(min_chunk_words=2, max_chunk_words=20, max_chunk_wait_ms=1000)

    chunks = chunker.feed("This is the first sentence. This is second")

    assert chunks == ["This is the first sentence."]
    assert chunker.flush() == ["This is second"]


def test_chunker_emits_one_sentence_at_a_time() -> None:
    chunker = SpeechChunker(min_chunk_words=2, max_chunk_words=20, max_chunk_wait_ms=1000)

    chunks = chunker.feed("First sentence. Second sentence. Third")

    assert chunks == ["First sentence."]
    assert chunker.flush() == ["Second sentence. Third"]


def test_chunker_does_not_emit_mid_sentence_on_timeout() -> None:
    chunker = SpeechChunker(min_chunk_words=2, max_chunk_words=20, max_chunk_wait_ms=50)

    assert chunker.feed("alpha beta", now_monotonic=1.0) == []
    timed_chunks = chunker.feed(" gamma", now_monotonic=1.2)

    assert timed_chunks == []
    assert chunker.flush() == ["alpha beta gamma"]


def test_chunker_strips_markdown_code_fragments() -> None:
    chunker = SpeechChunker(min_chunk_words=1, max_chunk_words=20, max_chunk_wait_ms=1000)

    chunks = chunker.feed("Use `rm -rf` carefully. ```python\nprint('x')\n``` done")
    chunks.extend(chunker.flush())

    assert chunks
    rendered = " ".join(chunks)
    assert "rm -rf" not in rendered
    assert "print('x')" not in rendered
    assert "Use" in rendered


def test_chunker_flushes_short_answer_without_early_emit() -> None:
    chunker = SpeechChunker(min_chunk_words=3, max_chunk_words=20, max_chunk_wait_ms=1000)

    assert chunker.feed("Sure") == []
    assert chunker.flush() == ["Sure"]


def test_chunker_keeps_waiting_buffer_on_timeout_without_sentence_end() -> None:
    chunker = SpeechChunker(min_chunk_words=2, max_chunk_words=20, max_chunk_wait_ms=50)

    assert chunker.feed("alpha beta gamma", now_monotonic=1.0) == []
    assert chunker.drain_on_timeout(now_monotonic=1.2) == []
    assert chunker.flush() == ["alpha beta gamma"]


def test_chunker_emits_on_paragraph_break() -> None:
    chunker = SpeechChunker(min_chunk_words=2, max_chunk_words=20, max_chunk_wait_ms=1000)

    chunks = chunker.feed("First paragraph line\n\nSecond paragraph starts")

    assert chunks == ["First paragraph line"]
    assert chunker.flush() == ["Second paragraph starts"]


def test_chunker_does_not_split_after_common_abbreviation() -> None:
    chunker = SpeechChunker(min_chunk_words=3, max_chunk_words=20, max_chunk_wait_ms=1000)

    chunks = chunker.feed("Use abbreviations like e.g. this example continues. Next sentence.")

    assert chunks == ["Use abbreviations like e.g. this example continues."]
    assert chunker.flush() == ["Next sentence."]


def test_chunker_does_not_split_inside_acronym() -> None:
    chunker = SpeechChunker(min_chunk_words=3, max_chunk_words=20, max_chunk_wait_ms=1000)

    chunks = chunker.feed("The U.S.A. team won today. Another sentence.")

    assert chunks == ["The U.S.A. team won today."]
    assert chunker.flush() == ["Another sentence."]


def test_chunker_does_not_split_inside_floating_point_number() -> None:
    chunker = SpeechChunker(min_chunk_words=3, max_chunk_words=20, max_chunk_wait_ms=1000)

    chunks = chunker.feed("Version 2.5 is stable now. Ship it.")

    assert chunks == ["Version 2.5 is stable now."]
    assert chunker.flush() == ["Ship it."]
