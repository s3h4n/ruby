"""STT provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class STTProvider(ABC):
    """Speech-to-text provider contract."""

    @abstractmethod
    def transcribe(self, audio_path: Path) -> str:
        """Return transcribed text for a local audio file."""
