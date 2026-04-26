## ADDED Requirements

### Requirement: Assistant core exposes reusable text and audio entrypoints
The system SHALL expose core assistant methods `handle_text(text: str)` and `handle_audio(audio_path: str)` that can be called by any interface.

#### Scenario: CLI text interface reuses core handler
- **WHEN** a text-based interface submits a user message
- **THEN** the interface calls `handle_text` and receives a structured assistant response without duplicating orchestration logic

### Requirement: Audio pipeline follows deterministic stage order
The system SHALL execute the v1 audio request flow in this order: capture/locate audio input, transcribe with configured STT provider, query configured LLM provider, optionally execute an approved tool call, and synthesize spoken output through configured TTS provider.

#### Scenario: Voice request produces spoken answer
- **WHEN** Ruby receives a valid voice command after wake activation
- **THEN** the system runs the configured pipeline stages in order and returns a short spoken response

### Requirement: Assistant response routing supports future intent extension
The system SHALL support structured response types `answer`, `tool_call`, and `intent` and SHALL return a non-failing fallback message for unsupported intents.

#### Scenario: Unsupported intent is safely handled
- **WHEN** the LLM returns `{ "type": "intent", "intent": "...", "args": {} }` for an unimplemented intent
- **THEN** Ruby responds with "That intent is not implemented yet." and performs no side effects
