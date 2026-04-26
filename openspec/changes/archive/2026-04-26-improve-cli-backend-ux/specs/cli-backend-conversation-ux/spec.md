## ADDED Requirements

### Requirement: CLI exposes clear pipeline state feedback
The CLI SHALL show a consistent, user-facing state progression for each request lifecycle and SHALL return to a ready prompt after completion.

#### Scenario: Voice request state progression
- **WHEN** the user submits an empty prompt input to trigger voice capture
- **THEN** the CLI shows `[Recording]`, `[Recorded]`, `[Transcribing]`, `[Thinking]`, `[Speaking]`, and `[Done]` in pipeline order

#### Scenario: Request loop readiness
- **WHEN** a response completes successfully
- **THEN** the CLI shows completion feedback and returns to a ready input prompt for the next request

### Requirement: CLI prompt supports mixed text and push-to-talk input
The CLI SHALL use a single prompt where empty input starts recording, typed non-command input is processed as text chat, and `/quit` exits the session.

#### Scenario: Empty input triggers recording
- **WHEN** the user presses Enter on an empty prompt
- **THEN** the assistant starts recording based on configured `record_seconds`

#### Scenario: Text input bypasses recording
- **WHEN** the user types a non-empty non-command message
- **THEN** the assistant sends that text directly to the LLM pipeline without audio recording

#### Scenario: Quit command exits cleanly
- **WHEN** the user enters `/quit`
- **THEN** the CLI exits without sending the command text to the LLM

### Requirement: CLI supports slash command controls
The CLI SHALL handle slash commands locally and SHALL NOT forward slash commands to the LLM provider.

#### Scenario: Help command
- **WHEN** the user enters `/help`
- **THEN** the CLI prints available commands and usage guidance

#### Scenario: Clear command
- **WHEN** the user enters `/clear`
- **THEN** the CLI clears in-session conversation history and confirms reset

#### Scenario: History command
- **WHEN** the user enters `/history`
- **THEN** the CLI prints recent retained user/assistant turns

#### Scenario: Status command
- **WHEN** the user enters `/status`
- **THEN** the CLI prints configured providers and selected model names

### Requirement: Session conversation history is retained and bounded
The backend SHALL maintain in-memory conversation history for the active session and SHALL apply turn-based trimming according to configuration.

#### Scenario: Follow-up prompt uses prior context
- **WHEN** the user asks a follow-up question in the same session
- **THEN** the LLM request includes relevant prior user and assistant messages so follow-up intent is preserved

#### Scenario: History trimming
- **WHEN** the number of user-assistant turns exceeds configured `conversation.max_turns`
- **THEN** the oldest turns are removed and only the most recent configured turns are retained

#### Scenario: History disabled
- **WHEN** `conversation.enabled` is set to false
- **THEN** only the current user message (plus system prompt) is sent for response generation

### Requirement: LLM provider accepts role-based message arrays
The LLM integration SHALL accept a role-based message list containing `system`, `user`, and `assistant` entries and SHALL send that list to Ollama `/api/chat` with `stream=false`.

#### Scenario: Ollama chat payload includes full history
- **WHEN** the backend invokes Ollama for a response
- **THEN** the request payload includes the full normalized `messages` array for the current session context

#### Scenario: Assistant history stores displayable text
- **WHEN** a response is received from the LLM provider
- **THEN** the assistant message stored in conversation history is human-readable reply text suitable for future context and `/history` output

### Requirement: User-facing errors are recoverable and informative
The CLI SHALL handle microphone, STT, LLM, and TTS failures without crashing and SHALL return to a usable ready state after each recoverable error.

#### Scenario: STT failure
- **WHEN** transcription fails for recorded audio
- **THEN** the CLI shows `[Error] Could not transcribe audio.` and returns to ready state

#### Scenario: Ollama unavailable
- **WHEN** LLM generation fails because Ollama is unreachable
- **THEN** the CLI shows `[Error] Ollama is not reachable. Start it with: ollama serve` and returns to ready state

#### Scenario: TTS failure after text generation
- **WHEN** speech playback fails after a text response is produced
- **THEN** the CLI shows the text response, prints `[Warning] Text response generated, but speech failed.`, and returns to ready state

#### Scenario: Microphone access failure
- **WHEN** microphone initialization or capture fails
- **THEN** the CLI shows `[Error] Microphone access failed. Check macOS privacy settings.` and returns to ready state

### Requirement: Debug output is configurable
The backend SHALL provide a `debug` configuration flag that controls whether internal runtime details are printed.

#### Scenario: Debug disabled
- **WHEN** `debug` is false
- **THEN** the CLI only prints clean user-facing statuses, transcript lines, assistant output, and command responses

#### Scenario: Debug enabled
- **WHEN** `debug` is true
- **THEN** the CLI includes internal diagnostic details such as provider metadata, subprocess details, and raw error context
