"""Provider factory for runtime selection from config."""

from __future__ import annotations

from ruby.config.settings import Settings
from ruby.core.errors import ProviderError
from ruby.providers.llm.base import LLMProvider
from ruby.providers.llm.ollama import OllamaLLMProvider
from ruby.providers.llm.openrouter import OpenRouterLLMProvider
from ruby.providers.search.base import SearchProvider
from ruby.providers.search.web_search_placeholder import WebSearchPlaceholderProvider
from ruby.providers.stt.base import STTProvider
from ruby.providers.stt.whisper_cpp import WhisperCppSTTProvider
from ruby.providers.tts.base import TTSProvider
from ruby.providers.tts.kokoro import KokoroTTSProvider


def build_stt_provider(settings: Settings) -> STTProvider:
    if settings.providers.stt.provider != "whisper_cpp":
        raise ProviderError(
            f"Unsupported STT provider: {settings.providers.stt.provider}. "
            "Only 'whisper_cpp' is supported in v1."
        )
    return WhisperCppSTTProvider(
        whisper_cli=settings.resolve_path(settings.providers.stt.whisper_cli),
        model_path=settings.resolve_path(settings.providers.stt.model),
    )


def build_llm_provider(settings: Settings) -> LLMProvider:
    provider_name = settings.providers.llm.provider
    if provider_name == "ollama":
        return OllamaLLMProvider(
            model=settings.providers.llm.model,
            url=settings.providers.llm.url,
        )

    if provider_name == "openrouter":
        return OpenRouterLLMProvider(model=settings.providers.llm.model)

    raise ProviderError(
        f"Unsupported LLM provider: {settings.providers.llm.provider}. "
        "Supported providers: 'ollama', 'openrouter'."
    )


def build_tts_provider(settings: Settings) -> TTSProvider:
    if settings.providers.tts.provider != "kokoro":
        raise ProviderError(
            f"Unsupported TTS provider: {settings.providers.tts.provider}. "
            "Only 'kokoro' is supported in v1."
        )
    return KokoroTTSProvider(voice=settings.providers.tts.voice)


def build_search_provider() -> SearchProvider:
    return WebSearchPlaceholderProvider(enabled=False)
