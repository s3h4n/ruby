## ADDED Requirements

### Requirement: Runtime SHALL use provider interfaces for STT, LLM, and TTS
The system SHALL define explicit base interfaces for STT, LLM, and TTS providers and SHALL instantiate configured implementations through provider selection logic.

#### Scenario: Configured provider resolves implementation
- **WHEN** config specifies `whisper_cpp`, `ollama`, and `kokoro`
- **THEN** runtime SHALL initialize matching provider implementations via factory logic

### Requirement: OpenRouter support SHALL be scaffolded but disabled by default
The system SHALL include an OpenRouter LLM provider module that reads env-based credentials but SHALL not run unless provider is explicitly configured.

#### Scenario: OpenRouter provider is not selected
- **WHEN** `providers.llm.provider` is `ollama`
- **THEN** OpenRouter provider code SHALL remain inactive and SHALL not affect runtime startup

### Requirement: Provider implementations SHALL avoid hardcoded model paths
STT/LLM/TTS implementations SHALL read model/path/voice values from configuration or env-derived provider settings instead of hardcoded constants.

#### Scenario: User switches configured model
- **WHEN** configured whisper or Ollama model value changes
- **THEN** runtime SHALL use updated values without code changes
