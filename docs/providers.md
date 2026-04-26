# Providers

Ruby uses provider interfaces for STT, LLM, and TTS so runtime components can be swapped by config.

## Contracts

- STT: `ruby/providers/stt/base.py`
- LLM: `ruby/providers/llm/base.py`
- TTS: `ruby/providers/tts/base.py`

Factory wiring is in `ruby/providers/factory.py`.

## Implementations

- STT: `ruby/providers/stt/whisper_cpp.py`
- LLM: `ruby/providers/llm/ollama.py`
- LLM placeholder: `ruby/providers/llm/openrouter.py`
- TTS: `ruby/providers/tts/kokoro.py`

## OpenRouter Placeholder Behavior

OpenRouter support is provided as a placeholder provider for OSS extension.

- It requires `OPENROUTER_API_KEY`.
- Missing key raises a clear setup error.
- Default configuration uses local Ollama (`providers.llm.provider = "ollama"`).

## Selection

Provider selection is driven by `config.json` (or fallback `config.example.json`).
Unsupported provider values raise explicit `ProviderError` messages at startup.
