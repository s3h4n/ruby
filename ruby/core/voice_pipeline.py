"""Streaming voice helpers for chunking, synthesis, and playback."""

from __future__ import annotations

from collections.abc import Callable
import queue
import re
import threading
import time
from pathlib import Path

from ruby.core.markdown_speech import markdown_to_speech_text
from ruby.providers.tts.base import TTSProvider


_WORD_PATTERN = re.compile(r"\b[\w']+\b")
_PUNCTUATION_BOUNDARY = re.compile(r"([.!?])\s+")
_PARAGRAPH_BOUNDARY = re.compile(r"\n\s*\n+")
_INLINE_CODE = re.compile(r"`[^`]*`")
_FENCED_CODE = re.compile(r"```[\s\S]*?```")
_COMMON_ABBREVIATION_END = re.compile(
    r"(?:\b(?:mr|mrs|ms|dr|prof|sr|jr|st|vs|etc|e\.g|i\.e)\.)$",
    re.IGNORECASE,
)
_ACRONYM_END = re.compile(r"(?:\b(?:[A-Za-z]\.){2,})$")
_DECIMAL_END = re.compile(r"\b\d+\.\d+$")


class SpeechChunker:
    """Buffers streaming text and emits natural speakable chunks."""

    def __init__(
        self,
        *,
        min_chunk_words: int,
        max_chunk_words: int,
        max_chunk_wait_ms: int,
    ) -> None:
        self.min_chunk_words = max(min_chunk_words, 1)
        self.max_chunk_words = max(max_chunk_words, self.min_chunk_words)
        self.max_chunk_wait_ms = max(max_chunk_wait_ms, 0)
        self._buffer = ""
        self._pending_since = 0.0

    def reset(self) -> None:
        self._buffer = ""
        self._pending_since = 0.0

    def feed(self, text_fragment: str, *, now_monotonic: float | None = None) -> list[str]:
        if not text_fragment:
            return []
        now = now_monotonic if now_monotonic is not None else time.monotonic()
        if not self._buffer:
            self._pending_since = now
        self._buffer += text_fragment
        return self._emit_ready(now)

    def flush(self) -> list[str]:
        if not self._buffer.strip():
            self.reset()
            return []
        chunk = self._sanitize_for_speech(self._buffer)
        self.reset()
        return [chunk] if chunk else []

    def drain_on_timeout(self, *, now_monotonic: float | None = None) -> list[str]:
        if not self._buffer.strip() or self.max_chunk_wait_ms <= 0 or self._pending_since <= 0.0:
            return []

        now = now_monotonic if now_monotonic is not None else time.monotonic()
        elapsed_ms = (now - self._pending_since) * 1000.0
        if elapsed_ms < self.max_chunk_wait_ms:
            return []

        return self._emit_ready(now)

    def _emit_ready(self, now_monotonic: float) -> list[str]:
        emitted: list[str] = []
        while self._buffer.strip():
            normalized = self._sanitize_for_speech(self._buffer)
            if not normalized:
                self.reset()
                break

            words = _WORD_PATTERN.findall(normalized)
            word_count = len(words)
            if word_count < self.min_chunk_words:
                break

            boundary = self._find_boundary(self._buffer)
            if boundary > 0:
                chunk = self._sanitize_for_speech(self._buffer[:boundary])
                self._buffer = self._buffer[boundary:].lstrip()
                if chunk:
                    emitted.append(chunk)
                self._pending_since = now_monotonic if self._buffer else 0.0
                break

            break

        return emitted

    def _find_boundary(self, text: str) -> int:
        words_seen = len(_WORD_PATTERN.findall(text))

        if words_seen < self.min_chunk_words:
            return -1

        candidates: list[int] = []
        for match in _PUNCTUATION_BOUNDARY.finditer(text):
            if match.group(1) == "." and self._is_protected_period(text, match.start()):
                continue
            candidate = match.end()
            candidates.append(candidate)

        for match in _PARAGRAPH_BOUNDARY.finditer(text):
            candidates.append(match.end())

        for candidate in sorted(set(candidates)):
            prefix = self._sanitize_for_speech(text[:candidate])
            count = len(_WORD_PATTERN.findall(prefix))
            if count >= self.min_chunk_words:
                return candidate

        return -1

    @staticmethod
    def _is_protected_period(text: str, period_index: int) -> bool:
        snippet = text[: period_index + 1].rstrip()[-32:]
        if _COMMON_ABBREVIATION_END.search(snippet):
            return True
        if _ACRONYM_END.search(snippet):
            return True
        if _DECIMAL_END.search(snippet):
            return True
        return False

    @staticmethod
    def _sanitize_for_speech(text: str) -> str:
        without_fences = _FENCED_CODE.sub(" ", text)
        without_inline = _INLINE_CODE.sub(" ", without_fences)
        normalized = markdown_to_speech_text(without_inline)
        return re.sub(r"\s+", " ", normalized).strip()


class TTSSynthesisQueue:
    """Worker-backed synthesis queue that emits audio paths asynchronously."""

    def __init__(
        self,
        *,
        tts_provider: TTSProvider,
        responses_dir: Path,
        cancel_event: threading.Event,
        on_first_audio_ready: Callable[[], None] | None = None,
    ) -> None:
        self._tts_provider = tts_provider
        self._responses_dir = responses_dir
        self._cancel_event = cancel_event
        self._on_first_audio_ready = on_first_audio_ready
        self._input_queue: queue.Queue[str | None] = queue.Queue()
        self.output_queue: queue.Queue[tuple[str, Path] | None] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._first_audio_reported = False
        self._counter = 0

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def enqueue(self, text: str) -> None:
        if text.strip():
            self._input_queue.put(text)

    def close(self) -> None:
        self._input_queue.put(None)

    def join(self, timeout: float | None = None) -> None:
        self._thread.join(timeout=timeout)

    def _run(self) -> None:
        self._responses_dir.mkdir(parents=True, exist_ok=True)
        try:
            while not self._cancel_event.is_set():
                item = self._input_queue.get()
                if item is None:
                    break

                self._counter += 1
                output_path = self._responses_dir / f"response-chunk-{int(time.time() * 1000)}-{self._counter}.wav"
                generated = self._tts_provider.synthesize(item, output_path)

                if not self._first_audio_reported and self._on_first_audio_ready is not None:
                    self._on_first_audio_ready()
                    self._first_audio_reported = True

                self.output_queue.put((item, generated))
        finally:
            self.output_queue.put(None)


class PlaybackQueue:
    """Plays synthesized chunk audio while synthesis continues."""

    def __init__(
        self,
        *,
        player: object,
        source_queue: queue.Queue[tuple[str, Path] | None],
        cancel_event: threading.Event,
        on_playback_start: Callable[[], None] | None = None,
        on_playback_stop: Callable[[], None] | None = None,
        on_chunk_start: Callable[[str, Path], None] | None = None,
        on_chunk_end: Callable[[], None] | None = None,
    ) -> None:
        self._player = player
        self._source_queue = source_queue
        self._cancel_event = cancel_event
        self._on_playback_start = on_playback_start
        self._on_playback_stop = on_playback_stop
        self._on_chunk_start = on_chunk_start
        self._on_chunk_end = on_chunk_end
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._started_playback = False

    def start(self) -> None:
        if not self._thread.is_alive():
            self._thread.start()

    def join(self, timeout: float | None = None) -> None:
        self._thread.join(timeout=timeout)

    def _run(self) -> None:
        try:
            while True:
                if self._cancel_event.is_set():
                    break

                item = self._source_queue.get()
                if item is None:
                    break

                text, audio_path = item

                if not self._started_playback and self._on_playback_start is not None:
                    self._on_playback_start()
                    self._started_playback = True

                if self._on_chunk_start is not None:
                    self._on_chunk_start(text, audio_path)

                try:
                    play_with_cancellation = getattr(self._player, "play_with_cancellation", None)
                    if callable(play_with_cancellation):
                        play_with_cancellation(audio_path, cancel_event=self._cancel_event)
                    else:
                        self._player.play(audio_path)
                finally:
                    if self._on_chunk_end is not None:
                        self._on_chunk_end()

                try:
                    audio_path.unlink(missing_ok=True)
                except OSError:
                    pass

                if self._cancel_event.is_set():
                    break
        finally:
            if self._on_playback_stop is not None:
                self._on_playback_stop()
