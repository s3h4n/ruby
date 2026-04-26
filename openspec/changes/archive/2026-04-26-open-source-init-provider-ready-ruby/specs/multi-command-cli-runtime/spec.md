## ADDED Requirements

### Requirement: CLI SHALL support command-based operational modes
The system SHALL support `init`, `run`, `doctor`, `models`, and `config` subcommands through `python app.py <command>`.

#### Scenario: User invokes explicit command
- **WHEN** a user executes `python app.py doctor`
- **THEN** Ruby SHALL execute doctor checks instead of starting the run loop

### Requirement: CLI SHALL preserve backward-compatible default run behavior
The system SHALL default to run mode when no command is provided.

#### Scenario: Legacy run invocation remains valid
- **WHEN** a user executes `python app.py` without arguments
- **THEN** Ruby SHALL behave as `python app.py run`

### Requirement: Config command SHALL print non-secret runtime configuration
The `config` command SHALL display current non-secret configuration fields and SHALL redact or omit secret values.

#### Scenario: Config output excludes API keys
- **WHEN** a user runs `python app.py config`
- **THEN** output SHALL include provider/model selections and SHALL not include any API key values
