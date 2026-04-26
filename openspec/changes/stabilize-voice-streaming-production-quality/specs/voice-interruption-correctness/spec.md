## ADDED Requirements

### Requirement: Barge-in detection SHALL ignore non-speech gaps between spoken chunks
When assistant playback has natural pauses between chunk audio files, the interruption detector SHALL NOT cancel the turn unless new user speech is actually detected.

#### Scenario: Silence gap between chunk playback does not interrupt
- **WHEN** chunk N playback ends, chunk N+1 is pending, and no user speech is present
- **THEN** the runtime keeps the turn active and continues playback of remaining chunks

### Requirement: Barge-in detection SHALL still stop active turns quickly
When user speech is detected while assistant audio is speaking, the runtime SHALL cancel active and pending work for that turn and surface interruption state.

#### Scenario: User speech during playback interrupts current turn
- **WHEN** assistant playback is active and recorder detects user speech above barge-in threshold
- **THEN** the runtime cancels generation/synthesis/playback for that turn and marks it interrupted
