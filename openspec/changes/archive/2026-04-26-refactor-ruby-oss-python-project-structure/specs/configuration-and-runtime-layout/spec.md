## ADDED Requirements

### Requirement: Settings are loaded from project config with explicit fallback
The system SHALL load settings from `config.json` when present, and SHALL otherwise load tracked defaults from `config.example.json`.

#### Scenario: Fallback to tracked defaults
- **WHEN** `config.json` is absent
- **THEN** runtime settings are loaded from `config.example.json`

### Requirement: Environment variables are loaded safely
The settings layer SHALL load `.env` values via `python-dotenv` when available, and SHALL NOT print secret values in command output or diagnostics.

#### Scenario: Secret values are redacted
- **WHEN** config-related output is rendered for users
- **THEN** sensitive values from environment or config are not printed in clear text

### Requirement: Runtime folders are local and auto-created
The runtime directories `recordings/`, `responses/`, `ruby_workspace/`, and `whisper.cpp/` SHALL be created as needed at runtime and SHALL remain untracked by default.

#### Scenario: Missing runtime folders are restored
- **WHEN** initialization or runtime checks run on a fresh clone
- **THEN** required runtime folders are created without committing them to source control

### Requirement: OSS-safe config tracking model is enforced
The repository SHALL track `config.example.json` and `.env.example`, and SHALL ignore `config.json` and `.env` in git.

#### Scenario: Local config is not tracked
- **WHEN** contributors generate local configuration via init flow
- **THEN** generated `config.json` and `.env` remain ignored by git
