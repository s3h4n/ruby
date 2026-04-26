"""Audio playback helpers."""

from __future__ import annotations

import subprocess
import threading
import time
from pathlib import Path

from ruby.core.errors import RubyError


class AudioPlayer:
    """Plays generated audio responses using macOS afplay."""

    def play(self, audio_path: Path) -> None:
        self.play_with_cancellation(audio_path, cancel_event=None)

    def play_with_cancellation(
        self,
        audio_path: Path,
        *,
        cancel_event: threading.Event | None,
    ) -> None:
        if not audio_path.exists():
            raise RubyError(f"Audio file not found for playback: {audio_path}")

        process = subprocess.Popen(
            ["afplay", str(audio_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        while process.poll() is None:
            if cancel_event is not None and cancel_event.is_set():
                process.terminate()
                process.wait(timeout=1)
                return
            time.sleep(0.05)

        if process.returncode != 0:
            stderr = process.stderr.read().strip() if process.stderr else ""
            stdout = process.stdout.read().strip() if process.stdout else ""
            raise RubyError(
                "Playback failed via afplay: "
                + (stderr or stdout or "unknown error")
            )
