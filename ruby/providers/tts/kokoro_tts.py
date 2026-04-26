"""Kokoro TTS provider implementation."""

from __future__ import annotations

import importlib
import io
import logging
import os
import warnings
import wave
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Iterable

from ruby.core.errors import ProviderError
from ruby.providers.tts.base import TTSProvider

# Suppress torch and transformers warnings that are not actionable by users
warnings.filterwarnings("ignore", category=UserWarning, module="torch.nn.modules.rnn")
warnings.filterwarnings("ignore", category=FutureWarning, module="torch.nn.utils.weight_norm")
warnings.filterwarnings("ignore", message=".*dropout.*expects num_layers.*")
# Suppress HuggingFace Hub warnings about unauthenticated requests
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")

# Suppress HF Hub logger
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


_KOKORO_SAMPLE_RATE = 24000
_KOKORO_LANG_CODES = {"a", "b", "e", "f", "h", "i", "p", "j", "z"}


class KokoroTTSProvider(TTSProvider):
    """Text-to-speech provider that expects local Kokoro package availability."""

    def __init__(self, voice: str) -> None:
        self.voice = voice
        self._module = None
        self._pipeline = None

    def _load_module(self) -> object:
        if self._module is not None:
            return self._module
        try:
            self._module = importlib.import_module("kokoro")
        except ModuleNotFoundError as exc:
            raise ProviderError(
                "Kokoro is not installed or importable. Install Kokoro in the active venv."
            ) from exc
        return self._module

    def synthesize(self, text: str, output_path: Path) -> Path:
        module = self._load_module()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # NOTE: Kokoro APIs vary by package build.
        # This implementation supports a common `synthesize_to_file` style hook.
        synthesize_to_file = getattr(module, "synthesize_to_file", None)
        if callable(synthesize_to_file):
            synthesize_to_file(text=text, voice=self.voice, output_path=str(output_path))
            if output_path.exists():
                return output_path

        # Fallback path attempts a generic class-based API.
        engine_cls = getattr(module, "Kokoro", None)
        if engine_cls is not None:
            engine = engine_cls()
            if hasattr(engine, "synthesize_to_file"):
                engine.synthesize_to_file(text=text, voice=self.voice, output_path=str(output_path))
                if output_path.exists():
                    return output_path

        if self._synthesize_via_kpipeline(module, text, output_path):
            return output_path

        raise ProviderError(
            "Kokoro API not recognized. Add a compatible local Kokoro adapter in "
            "ruby/providers/tts/kokoro_tts.py for your installed Kokoro package."
        )

    def _synthesize_via_kpipeline(self, module: object, text: str, output_path: Path) -> bool:
        pipeline_cls = getattr(module, "KPipeline", None)
        if pipeline_cls is None:
            return False

        if self._pipeline is None:
            lang_code = self._infer_lang_code(self.voice)
            # Suppress HF Hub warnings during pipeline initialization.
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    try:
                        # Preferred initialization for newer Kokoro builds.
                        self._pipeline = pipeline_cls(
                            lang_code=lang_code,
                            repo_id="hexgrad/Kokoro-82M",
                        )
                    except TypeError:
                        # Backward compatibility for older KPipeline signatures.
                        self._pipeline = pipeline_cls(lang_code=lang_code)

        with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            try:
                results = self._pipeline(text=text, voice=self.voice)
            except TypeError:
                results = self._pipeline(text, self.voice)

        samples: list[float] = []
        for result in results:
            audio = getattr(result, "audio", None)
            if audio is None:
                output = getattr(result, "output", None)
                if output is not None:
                    audio = getattr(output, "audio", None)
            if audio is None:
                continue
            samples.extend(self._coerce_audio_samples(audio))

        if not samples:
            return False

        self._write_wav(output_path, samples, _KOKORO_SAMPLE_RATE)
        return output_path.exists()

    @staticmethod
    def _infer_lang_code(voice: str) -> str:
        voice_prefix = voice.strip().lower().split("_", 1)[0]
        if voice_prefix:
            lang_code = voice_prefix[0]
            if lang_code in _KOKORO_LANG_CODES:
                return lang_code
        return "a"

    def _coerce_audio_samples(self, audio: object) -> list[float]:
        if hasattr(audio, "detach"):
            audio = audio.detach()
        if hasattr(audio, "cpu"):
            audio = audio.cpu()
        if hasattr(audio, "tolist"):
            audio = audio.tolist()
        return [float(v) for v in self._flatten(audio)]

    def _flatten(self, values: object) -> Iterable[float]:
        if isinstance(values, (list, tuple)):
            for value in values:
                yield from self._flatten(value)
            return
        yield float(values)

    @staticmethod
    def _write_wav(output_path: Path, samples: list[float], sample_rate: int) -> None:
        clipped = [max(-1.0, min(1.0, sample)) for sample in samples]
        pcm = [int(sample * 32767.0) for sample in clipped]
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            frames = bytearray()
            for value in pcm:
                frames.extend(int(value).to_bytes(2, byteorder="little", signed=True))
            wav_file.writeframes(bytes(frames))
