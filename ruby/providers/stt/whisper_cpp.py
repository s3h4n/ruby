"""whisper.cpp STT provider implementation."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ruby.core.errors import ProviderError
from ruby.providers.stt.base import STTProvider


class WhisperCppSTTProvider(STTProvider):
    """Speech-to-text via local whisper.cpp CLI."""

    def __init__(self, whisper_cli: Path, model_path: Path) -> None:
        self.whisper_cli = whisper_cli
        self.model_path = model_path

    def transcribe(self, audio_path: Path) -> str:
        if not self.whisper_cli.exists():
            raise ProviderError(
                "whisper-cli binary not found. Build whisper.cpp and update providers.stt.whisper_cli."
            )
        if not self.model_path.exists():
            raise ProviderError(
                "Whisper model is missing. Configure providers.stt.model or WHISPER_MODEL_PATH."
            )
        if not audio_path.exists():
            raise ProviderError("Audio file for transcription is missing.")

        output_base = audio_path.with_suffix("")
        command = [
            str(self.whisper_cli),
            "-m",
            str(self.model_path),
            "-f",
            str(audio_path),
            "-otxt",
            "-of",
            str(output_base),
            "-nt",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise ProviderError(
                "whisper.cpp transcription failed: "
                + (result.stderr.strip() or result.stdout.strip() or "unknown error")
            )

        transcript_path = output_base.with_suffix(".txt")
        if not transcript_path.exists():
            raise ProviderError(
                "whisper.cpp completed but transcript file was not created."
            )

        transcript = transcript_path.read_text(encoding="utf-8").strip()
        if not transcript:
            raise ProviderError("Transcription was empty. Please try speaking again.")
        return transcript
