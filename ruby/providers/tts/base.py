"""TTS provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TTSProvider(ABC):
    """Text-to-speech provider contract."""

    @abstractmethod
    def synthesize(self, text: str, output_path: Path) -> Path:
        """Write speech audio to output_path and return final path."""
