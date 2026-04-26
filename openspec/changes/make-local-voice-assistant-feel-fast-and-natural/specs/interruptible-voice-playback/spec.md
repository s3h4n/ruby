## ADDED Requirements

### Requirement: Barge-in SHALL cancel active assistant speech flow
When barge-in is enabled and user speech is detected during assistant speaking, the runtime SHALL cancel pending response generation, pending synthesis, and queued playback for the interrupted turn.

#### Scenario: User interrupts while assistant is speaking
- **WHEN** assistant playback is active and new user speech is detected
- **THEN** the runtime marks the current turn as interrupted and cancels remaining generation/synthesis/playback work for that turn

### Requirement: Playback stop latency SHALL be measured on interruption
The runtime SHALL measure interruption stop latency from barge-in detection to playback halt and SHALL expose this metric in debug latency output.

#### Scenario: Interruption latency is logged
- **WHEN** a barge-in interruption occurs and debug latency logging is enabled
- **THEN** the runtime logs the measured time between interruption detection and playback stop

### Requirement: Interruption status SHALL be visible in CLI feedback
The CLI runtime SHALL display interruption-related state transitions to make cancellation behavior visible.

#### Scenario: CLI reports interruption state
- **WHEN** barge-in is detected during speech
- **THEN** the CLI shows interruption and stop/listening transitions in runtime output

### Requirement: Interrupted assistant output SHALL not be committed as complete
If a response is interrupted, the runtime SHALL NOT store the interrupted assistant text as a completed assistant conversation message.

#### Scenario: Interrupted response is excluded from completed history
- **WHEN** a response is cancelled due to barge-in
- **THEN** the conversation history stores the user transcript but does not add a completed assistant reply for the cancelled turn
