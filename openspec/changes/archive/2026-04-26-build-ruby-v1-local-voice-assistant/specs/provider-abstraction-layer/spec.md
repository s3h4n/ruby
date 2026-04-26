## ADDED Requirements

### Requirement: STT, LLM, and TTS provider contracts must be explicit
The system SHALL define explicit provider interfaces for STT, LLM, and TTS behavior, and runtime logic MUST depend on these interfaces rather than concrete provider implementations.

#### Scenario: Core runtime is provider-agnostic
- **WHEN** the assistant runtime initializes providers
- **THEN** it interacts through contract methods and does not directly call provider-specific binaries or APIs from core orchestration code

### Requirement: Local v1 provider implementations must be available and selectable by config
The system SHALL provide `WhisperCppSTTProvider`, `OllamaLLMProvider`, and `KokoroTTSProvider`, and SHALL select providers using `config.json` provider identifiers.

#### Scenario: Config selects local providers successfully
- **WHEN** config sets STT=`whisper_cpp`, LLM=`ollama`, and TTS=`kokoro`
- **THEN** Ruby initializes the corresponding provider classes and processes requests without code changes

### Requirement: Search provider extension point exists but remains disabled in v1
The system SHALL include a search provider abstraction and placeholder implementation that is disabled by default and not invoked during v1 runtime.

#### Scenario: v1 runtime avoids search execution
- **WHEN** Ruby starts with default v1 configuration
- **THEN** no search provider calls are executed and the placeholder remains inactive
