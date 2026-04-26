## ADDED Requirements

### Requirement: Recording mode SHALL be configurable
The assistant SHALL support `recording_mode` values `vad`, `fixed`, and `manual`, and SHALL default to `vad`.

#### Scenario: Default recording mode uses VAD
- **WHEN** no recording mode override is provided
- **THEN** the runtime uses `vad` as the active recording mode

### Requirement: VAD mode SHALL detect speech boundaries
In `vad` mode, the runtime SHALL detect speech start, detect speech end after configured silence, include configurable pre-roll audio, and enforce minimum speech duration before accepting a turn.

#### Scenario: Turn closes after post-speech silence
- **WHEN** speech is detected and then silence exceeds configured `silence_end_ms`
- **THEN** the runtime finalizes the turn and sends only the completed segment for transcription

### Requirement: VAD mode SHALL enforce turn duration bounds
In `vad` mode, the runtime SHALL end capture when `max_turn_seconds` is reached to avoid unbounded recording.

#### Scenario: Long turn is capped by max duration
- **WHEN** active speech capture reaches configured `max_turn_seconds`
- **THEN** the runtime finalizes the captured segment and proceeds to transcription

### Requirement: Fixed and manual capture SHALL remain available
The runtime SHALL preserve fixed-duration capture and manual capture behaviors as fallback/debug-compatible modes.

#### Scenario: Fixed mode records for configured duration
- **WHEN** `recording_mode` is set to `fixed`
- **THEN** the runtime captures audio using the configured fixed recording duration path instead of VAD
