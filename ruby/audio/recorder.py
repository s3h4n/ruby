"""Audio recording helpers."""

from __future__ import annotations

import threading
from pathlib import Path

from ruby.core.errors import RubyError, StartupCheckError


class AudioRecorder:
    """Records microphone audio to local files."""

    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate

    def check_microphone_access(self) -> None:
        try:
            import sounddevice as sd
        except ModuleNotFoundError as exc:
            raise StartupCheckError(
                "Missing package 'sounddevice'. Install required audio dependencies."
            ) from exc

        try:
            sd.check_input_settings(samplerate=self.sample_rate, channels=1)
        except Exception as exc:  # noqa: BLE001
            raise StartupCheckError(
                "Microphone is unavailable. Grant microphone permission in "
                "System Settings -> Privacy & Security -> Microphone, then retry."
            ) from exc

    def record(
        self,
        seconds: int,
        output_path: Path,
        *,
        stop_event: threading.Event | None = None,
        cancel_event: threading.Event | None = None,
    ) -> Path | None:
        try:
            import numpy as np
            import sounddevice as sd
            import soundfile as sf
        except ModuleNotFoundError as exc:
            raise StartupCheckError(
                "Missing sounddevice/soundfile packages. Activate your project venv."
            ) from exc

        output_path.parent.mkdir(parents=True, exist_ok=True)
        stop_event = stop_event or threading.Event()
        cancel_event = cancel_event or threading.Event()

        total_frames = int(seconds * self.sample_rate)
        chunk_frames = max(int(self.sample_rate * 0.2), 1)
        captured: list = []
        recorded_frames = 0

        while recorded_frames < total_frames and not stop_event.is_set() and not cancel_event.is_set():
            current_frames = min(chunk_frames, total_frames - recorded_frames)
            chunk = sd.rec(current_frames, samplerate=self.sample_rate, channels=1, dtype="float32")
            sd.wait()
            captured.append(chunk)
            recorded_frames += current_frames

        if cancel_event.is_set() and not stop_event.is_set():
            return None
        if not captured:
            raise RubyError("No audio captured. Please try again.")

        audio_data = np.concatenate(captured, axis=0)
        sf.write(str(output_path), audio_data, self.sample_rate)
        return output_path
