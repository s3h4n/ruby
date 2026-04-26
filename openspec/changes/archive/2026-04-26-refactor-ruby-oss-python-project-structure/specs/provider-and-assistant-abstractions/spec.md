## ADDED Requirements

### Requirement: Assistant core provides text and audio handling contracts
The core assistant module SHALL expose a `RubyAssistant` class with `handle_text(text: str) -> AssistantResponse` and `handle_audio(audio_path: str) -> AssistantResponse` methods.

#### Scenario: Voice flow delegates to assistant core
- **WHEN** the runtime receives audio input from recording or wake flow
- **THEN** processing passes through `RubyAssistant.handle_audio` instead of CLI-owned business logic

### Requirement: Assistant response schemas are explicit dataclasses
The core schemas module SHALL define dataclasses for `AssistantResponse` and `ToolResult` with fields needed for response text and tool execution outcomes.

#### Scenario: Tool outcomes map to typed results
- **WHEN** a tool invocation succeeds or fails
- **THEN** the result is represented as a `ToolResult` object with success state and message

### Requirement: Provider interfaces define minimum behavior
The providers layer SHALL define base contracts for `STTProvider.transcribe(audio_path: str) -> str`, `LLMProvider.chat(messages: list[dict]) -> dict`, and `TTSProvider.speak_to_file(text: str, output_path: str) -> str`.

#### Scenario: Provider implementations satisfy common contract
- **WHEN** assistant orchestration switches between provider implementations
- **THEN** it interacts through provider interfaces without changing core assistant logic

### Requirement: Local providers are first-class and OpenRouter is placeholder-only
The project SHALL include provider implementations for Whisper (`whisper_cpp.py`), Ollama (`ollama.py`), and Kokoro (`kokoro.py`), and SHALL include `openrouter.py` as a disabled placeholder that raises a clear configuration error when `OPENROUTER_API_KEY` is missing.

#### Scenario: OpenRouter is not enabled by default
- **WHEN** OpenRouter provider is selected without required environment configuration
- **THEN** the provider fails fast with a clear setup error and does not silently fall back
