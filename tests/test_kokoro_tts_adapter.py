from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from ruby.providers.tts.kokoro_tts import KokoroTTSProvider


class _FakeResult:
    def __init__(self, audio: list[float]) -> None:
        self.audio = audio


class _FakeKPipeline:
    def __init__(self, lang_code: str) -> None:
        self.lang_code = lang_code

    def __call__(self, text: str, voice: str, speed: float = 1.0):
        del text, voice, speed
        yield _FakeResult([0.0, 0.2, -0.2, 0.0])


class KokoroAdapterTests(unittest.TestCase):
    def test_synthesize_supports_kpipeline_style_api(self) -> None:
        fake_module = types.SimpleNamespace(KPipeline=_FakeKPipeline)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "tts.wav"
            provider = KokoroTTSProvider(voice="af_bella")
            with mock.patch("ruby.providers.tts.kokoro_tts.importlib.import_module", return_value=fake_module):
                result = provider.synthesize("hello", output_path)

            self.assertEqual(result, output_path)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
