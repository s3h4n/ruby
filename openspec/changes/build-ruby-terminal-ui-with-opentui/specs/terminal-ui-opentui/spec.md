## ADDED Requirements

### Requirement: TUI launch path and CLI compatibility
The system SHALL provide a TUI launch command from the canonical Python CLI while preserving the existing runner command behavior.

#### Scenario: User launches TUI from CLI
- **WHEN** the user runs `python app.py tui`
- **THEN** Ruby SHALL start the OpenTUI frontend connected to the Python runtime bridge

#### Scenario: Existing runner remains available
- **WHEN** the user runs `python app.py run`
- **THEN** existing runner behavior SHALL remain functionally unchanged

### Requirement: Three-part terminal layout
The TUI SHALL render a three-part layout: header, main conversation view, and footer/input area.

#### Scenario: Header displays runtime context
- **WHEN** the TUI is active
- **THEN** the header SHALL show app identity, active model, input mode, workspace path, and runtime status summary

#### Scenario: Footer displays current state and actions
- **WHEN** runtime state changes
- **THEN** the footer SHALL update to show current state, a plain-English explanation, and valid next actions

### Requirement: Conversation rendering and streaming visibility
The TUI SHALL show user messages, streaming assistant output, and useful system notes with readable wrapping.

#### Scenario: Voice message appears after transcription
- **WHEN** recording stops and transcription completes
- **THEN** the conversation SHALL show a user message labeled as voice input before assistant thinking/streaming output begins

#### Scenario: Assistant response streams live
- **WHEN** assistant delta events are received
- **THEN** the active assistant message SHALL update incrementally in the conversation view until done

### Requirement: Tool activity visibility
The TUI SHALL display active and completed tool activity in a compact panel or inline status region.

#### Scenario: Tool lifecycle reflected in UI
- **WHEN** the runtime emits `tool.started` and `tool.finished`
- **THEN** the TUI SHALL show tool name, operation context, and completion status
- **AND** failed tool activity SHALL be visually distinguishable from success

### Requirement: State transparency and recoverable errors
The TUI SHALL make runtime progress and failures explicit so users can always tell what Ruby is doing now and what action to take next.

#### Scenario: Runtime enters transcribing state
- **WHEN** the runtime emits `state.changed` with `transcribing`
- **THEN** the UI SHALL show a visible transcribing state label and guidance text

#### Scenario: Recoverable error displayed
- **WHEN** an `error` event is received
- **THEN** the UI SHALL display a plain-English failure message with likely cause and recovery action
- **AND** stack traces SHALL be hidden unless debug mode is enabled

### Requirement: Keyboard control support
The TUI SHALL support keyboard control for send/recording stop, pause/resume, interrupt, clear conversation, voice start, text mode switch, and shortcut help.

#### Scenario: Interrupt shortcut is used
- **WHEN** the user presses `Ctrl+C` during thinking, streaming, or speaking
- **THEN** the TUI SHALL send `assistant.interrupt` to the backend
- **AND** the UI SHALL preserve partial assistant content and show an interruption note

#### Scenario: Shortcut conflict occurs
- **WHEN** a required shortcut is not safely available in terminal context
- **THEN** the TUI SHALL provide the nearest safe alternative
- **AND** documentation SHALL list the mapped alternative

### Requirement: Mock mode for frontend development
The TUI SHALL provide a mock runtime mode that can run without live voice/model dependencies.

#### Scenario: Standard lifecycle simulation
- **WHEN** the user runs `bun run tui:mock`
- **THEN** mock mode SHALL simulate idle, recording, transcribing, user message, thinking, streaming, speaking, and idle transitions

#### Scenario: Failure and control simulation
- **WHEN** mock mode is active
- **THEN** it SHALL support simulated interrupt-during-thinking, interrupt-during-streaming, pause-during-speaking, backend error, and terminal resize events

### Requirement: Terminal resize handling
The TUI SHALL keep conversation and status regions usable after terminal dimension changes.

#### Scenario: Terminal window resizes
- **WHEN** terminal size changes while TUI is running
- **THEN** layout regions SHALL recompute without crashing
- **AND** active conversation and status context SHALL remain visible
