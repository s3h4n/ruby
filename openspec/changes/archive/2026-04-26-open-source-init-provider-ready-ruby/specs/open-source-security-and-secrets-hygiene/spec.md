## ADDED Requirements

### Requirement: Secret hygiene SHALL separate secrets from tracked config
The system SHALL keep `config.json` non-secret and SHALL store sensitive provider credentials in `.env` loaded via `python-dotenv`.

#### Scenario: API key configuration is required
- **WHEN** a provider requires an API key
- **THEN** key material SHALL be read from environment variables and SHALL never be printed in logs or config output

### Requirement: Model operation subprocesses SHALL be allowlisted and non-shell
The system SHALL execute model download/pull operations using argument-array subprocess calls and fixed allowlists for accepted model identifiers.

#### Scenario: User attempts unsupported model identifier
- **WHEN** a model identifier outside allowlist is requested in managed download/pull flow
- **THEN** operation SHALL be rejected without executing subprocess

### Requirement: Workspace and tool safety constraints SHALL remain enforced
File tool operations SHALL remain restricted to `ruby_workspace` and SHALL block traversal or destructive operations in v1.

#### Scenario: Path traversal attempt
- **WHEN** a tool call includes `../` path escapes
- **THEN** operation SHALL be denied with safety error and no filesystem write outside workspace
