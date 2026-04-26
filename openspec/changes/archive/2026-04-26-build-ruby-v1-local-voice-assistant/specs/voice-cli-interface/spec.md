## ADDED Requirements

### Requirement: Root runner must delegate to interface entrypoint
The root `app.py` SHALL only import and call `ruby.interfaces.cli.main` as the application entrypoint.

#### Scenario: Root startup path remains thin
- **WHEN** a user runs `python app.py`
- **THEN** execution enters the CLI interface main function without embedding business logic in root runner code

### Requirement: Voice CLI loop must support wake-driven command capture
The voice CLI SHALL support wake-word-enabled operation where Ruby waits for wake trigger and records the subsequent command audio for processing.

#### Scenario: Wake mode captures a command
- **WHEN** wake-word mode is enabled and trigger criteria are met
- **THEN** Ruby records command audio and sends it to assistant core for handling

### Requirement: Voice CLI must provide an operational fallback path
The interface SHALL provide a push-to-talk or manual capture fallback path when wake detection is unavailable or unreliable.

#### Scenario: Fallback mode keeps assistant usable
- **WHEN** wake detection cannot be used on the host system
- **THEN** the user can still record and submit commands through a documented fallback interaction

### Requirement: Interface and core concerns must remain separated
The interface SHALL handle I/O and session loop concerns only, and core assistant orchestration MUST remain in the assistant package APIs.

#### Scenario: Tool and provider logic stays out of interface module
- **WHEN** interface code receives a command
- **THEN** it delegates processing to assistant core methods and does not directly execute provider or tool business logic
