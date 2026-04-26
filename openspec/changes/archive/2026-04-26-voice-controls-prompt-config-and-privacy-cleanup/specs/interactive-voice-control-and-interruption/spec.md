## ADDED Requirements

### Requirement: Enter key toggles recording start and stop
The CLI runtime SHALL treat Enter as a state-dependent recording toggle: Enter starts recording from `[Ready]`, and Enter stops recording immediately from `[Recording]`.

#### Scenario: Start recording with Enter
- **WHEN** Ruby is in `[Ready]` state and the user presses Enter
- **THEN** Ruby transitions to `[Recording]` and begins capturing audio

#### Scenario: Stop recording with Enter
- **WHEN** Ruby is in `[Recording]` state and the user presses Enter
- **THEN** Ruby finalizes the current recording and continues to `[Recorded]` for normal downstream processing

### Requirement: Timeout auto-stop remains available
The runtime MUST preserve timeout-based recording stop as fallback behavior when manual stop is not triggered.

#### Scenario: Timeout fallback stop
- **WHEN** Ruby is in `[Recording]` state and the recording timeout is reached without a manual stop
- **THEN** Ruby finalizes recording and continues through the existing post-recording flow

### Requirement: User interruption returns safely to ready state
The runtime MUST support interruption via `Esc` or `Ctrl+C` during recording, transcribing, thinking, or speaking and return to `[Ready]` safely.

#### Scenario: Interrupt from active stage
- **WHEN** Ruby is in any active stage (`[Recording]`, `[Transcribing]`, `[Thinking]`, or `[Speaking]`) and user interruption is received
- **THEN** Ruby emits clean output including `[Interrupted]` and returns to `[Ready]` without exposing stack traces during normal interruption
