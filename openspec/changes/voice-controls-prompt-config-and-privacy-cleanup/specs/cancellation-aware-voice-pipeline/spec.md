## ADDED Requirements

### Requirement: Shared cancellation signal is used across long-running stages
Ruby MUST use a shared cancellation mechanism for active voice-session work so recording, transcription, model generation, and speaking can be interrupted consistently.

#### Scenario: Cancellation signal propagation
- **WHEN** a user interruption occurs during an active voice session
- **THEN** the same cancellation signal is visible to recording, transcription, thinking, and speaking stages

### Requirement: Canceled stage output is not allowed to continue downstream
If cancellation is signaled, the pipeline SHALL prevent canceled stage outputs from being processed in later states.

#### Scenario: Cancellation during transcription
- **WHEN** cancellation occurs while transcription is running
- **THEN** transcription processing stops and no transcription result is forwarded to thinking

#### Scenario: Cancellation during thinking when request cannot be physically aborted
- **WHEN** cancellation is set during model generation and the provider cannot cancel in-flight work
- **THEN** any late result is ignored and MUST NOT trigger speaking

### Requirement: Speaking interruption stops playback immediately
When cancellation is signaled during speaking, playback MUST stop immediately and the session returns to `[Ready]`.

#### Scenario: Cancellation during speaking
- **WHEN** Ruby is in `[Speaking]` and interruption is received
- **THEN** TTS playback stops promptly and Ruby transitions to `[Ready]`

### Requirement: Partial recording data is discarded on canceled recording
If recording is interrupted before finalization, Ruby SHALL discard partial capture data unless recording had already been finalized.

#### Scenario: Cancellation during recording before finalization
- **WHEN** interruption occurs while recording and audio has not been finalized
- **THEN** partial audio is discarded and no recording is sent for transcription
