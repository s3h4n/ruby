"""Wake trigger helpers for voice runtime."""

from __future__ import annotations

import time


class WakeWordDetector:
    """Simple local wake trigger detector.

    v1 uses an energy threshold trigger. If live audio detection fails,
    callers should use push-to-talk/manual fallback.
    """

    def __init__(
        self,
        enabled: bool,
        threshold: float,
        chunk_size: int,
        sample_rate: int,
    ) -> None:
        self.enabled = enabled
        self.threshold = threshold
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate

    def wait_for_trigger(self, timeout_seconds: int | None = None) -> bool:
        if not self.enabled:
            return True

        try:
            import numpy as np
            import sounddevice as sd
        except ModuleNotFoundError:
            return False

        start = time.monotonic()
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=self.chunk_size,
        ) as stream:
            while True:
                data, _ = stream.read(self.chunk_size)
                level = float(np.abs(data).mean())
                if level >= self.threshold:
                    return True
                if timeout_seconds is not None and (time.monotonic() - start) > timeout_seconds:
                    return False
