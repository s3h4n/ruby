## ADDED Requirements

### Requirement: Voice responses SHALL use spoken-first style
In voice mode, assistant responses SHALL prioritize concise spoken phrasing, start with useful content, and avoid markdown-heavy formatting unless explicitly requested.

#### Scenario: Simple question gets direct short answer
- **WHEN** the user asks a short factual question
- **THEN** the assistant returns a direct concise spoken answer without unnecessary filler

### Requirement: Long or tool-like tasks SHALL receive brief acknowledgement
For long-running or tool-like requests, the assistant SHALL emit a short natural acknowledgement before the main response work continues.

#### Scenario: Long task starts with acknowledgement
- **WHEN** the user request is classified as long-running or tool-like
- **THEN** the assistant emits a brief acknowledgement phrase before continuing with task output

### Requirement: CLI SHALL expose clear runtime states
During voice interaction, the CLI SHALL show state feedback covering listening, transcription, thinking, speaking, interruption, and completion.

#### Scenario: States progress through a normal turn
- **WHEN** the user completes a normal voice turn without interruption
- **THEN** the CLI displays state transitions including listening, transcribing, thinking, speaking, and done

### Requirement: Latency checkpoints SHALL be available in debug mode
When debug latency logging is enabled, the runtime SHALL emit timing checkpoints for speech-end-to-transcript, transcript-to-first-token, first-token-to-first-chunk, first-chunk-to-first-TTS-audio, and first-TTS-audio-to-playback-start.

#### Scenario: Debug timing output includes key checkpoints
- **WHEN** a voice turn completes with debug latency logging enabled
- **THEN** the CLI outputs timing values for the configured pipeline checkpoint stages
