## ADDED Requirements

### Requirement: Frontend bridge transport
The system SHALL provide a frontend bridge transport that exchanges command and event messages as line-delimited JSON between the OpenTUI frontend process and the Python runtime process.

#### Scenario: Runtime starts in frontend mode
- **WHEN** the frontend launches the backend bridge process for interactive runtime control
- **THEN** the backend SHALL emit structured JSON event objects on stdout
- **AND** the frontend SHALL send structured JSON command objects on stdin

### Requirement: Runtime state event emission
The runtime SHALL emit `state.changed` events with `state`, `message`, and `timestamp`, and the `state` value SHALL be one of: `idle`, `recording`, `transcribing`, `thinking`, `streaming`, `speaking`, `paused`, `interrupted`, or `error`.

#### Scenario: State transition is published
- **WHEN** the runtime transitions from one lifecycle state to another
- **THEN** it SHALL publish a `state.changed` event containing the new state and a human-readable message

### Requirement: Conversation stream events
The runtime SHALL emit conversation events for user input and assistant output using `conversation.user`, `conversation.assistant.delta`, and `conversation.assistant.done`.

#### Scenario: Voice input roundtrip is bridged
- **WHEN** voice recording is started and then stopped
- **THEN** the runtime SHALL emit `state.changed` events for `recording` and `transcribing`
- **AND** after transcription completes it SHALL emit `conversation.user` with the transcribed content before assistant generation begins

#### Scenario: Assistant response streams to frontend
- **WHEN** the assistant generates a response
- **THEN** the runtime SHALL emit one or more `conversation.assistant.delta` events with incremental content
- **AND** it SHALL emit `conversation.assistant.done` when streaming is complete

### Requirement: Tool lifecycle events
The runtime SHALL emit `tool.started` and `tool.finished` events with tool identity, operation details, and completion status.

#### Scenario: Tool execution succeeds
- **WHEN** a tool is invoked by the assistant
- **THEN** the runtime SHALL emit `tool.started` with `name`, `description`, and `timestamp`
- **AND** on completion it SHALL emit `tool.finished` with the same `name`, a success status, and `timestamp`

#### Scenario: Tool execution fails
- **WHEN** a tool invocation fails
- **THEN** the runtime SHALL emit `tool.finished` with failure status
- **AND** it SHALL also emit an `error` event with scope `tool` and recovery guidance

### Requirement: Frontend command contract
The backend SHALL accept these frontend commands: `input.text`, `voice.start`, `voice.stop`, `assistant.interrupt`, `assistant.pause`, `assistant.resume`, and `conversation.clear_visible`.

#### Scenario: Text input command is received
- **WHEN** the frontend sends an `input.text` command with content
- **THEN** the backend SHALL process the content as a user message and emit corresponding conversation and state events

#### Scenario: Unknown command is received
- **WHEN** the frontend sends a command type not in the command contract
- **THEN** the backend SHALL reject it gracefully without crashing
- **AND** it SHALL emit an `error` event with scope `bridge` including recovery guidance

### Requirement: Interrupt and pause semantics
The runtime SHALL support pause/resume and interrupt control through bridge commands without losing already produced assistant output.

#### Scenario: Interrupt during streaming
- **WHEN** the frontend sends `assistant.interrupt` while assistant output is streaming
- **THEN** the runtime SHALL stop ongoing generation or speaking activity
- **AND** it SHALL emit `state.changed` to `interrupted` followed by `idle`
- **AND** previously streamed assistant content SHALL remain available to the frontend

#### Scenario: Pause and resume during speaking
- **WHEN** the frontend sends `assistant.pause` while speech output is active
- **THEN** the runtime SHALL transition to `paused`
- **AND** when `assistant.resume` is received it SHALL continue speaking and then return to `idle` on completion

### Requirement: Runtime error events
The runtime SHALL emit user-recoverable `error` events that include `scope`, `message`, `cause`, `recovery`, and `timestamp`.

#### Scenario: Model backend unavailable
- **WHEN** the runtime cannot reach the configured local model backend
- **THEN** it SHALL emit an `error` event with scope `model`
- **AND** `message`, `cause`, and `recovery` SHALL be plain English guidance appropriate for terminal display
