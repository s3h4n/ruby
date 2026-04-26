## ADDED Requirements

### Requirement: Tool execution must be registry-driven and metadata-governed
The system SHALL execute tools only when they are registered with name, description, argument structure, risk level, and enabled status.

#### Scenario: Disabled tool is rejected
- **WHEN** a tool call references a known tool that is not enabled
- **THEN** Ruby refuses execution and reports that the tool is unavailable

### Requirement: V1 tool set must be explicitly limited
The system SHALL expose only these v1 tools for LLM-triggered execution: `get_time`, `open_app`, `list_directory`, `create_folder`, and `create_file`.

#### Scenario: Unsupported tool call is blocked
- **WHEN** the model requests a tool outside the allowed v1 tool set
- **THEN** Ruby denies the action and returns a safe unsupported-capability response

### Requirement: File tools must enforce workspace sandbox boundaries
The system SHALL allow file operations only within `ruby_workspace/`, SHALL prevent path traversal, and SHALL disallow delete operations in v1.

#### Scenario: Traversal attempt is denied
- **WHEN** a file tool request attempts to access `../` or a path outside `ruby_workspace/`
- **THEN** Ruby blocks the operation and returns a safety error response

### Requirement: App launching must use allowlisted application aliases
The `open_app` tool SHALL map user-friendly aliases to explicit allowed macOS app names from configuration and SHALL reject unknown app names.

#### Scenario: Unknown app request is rejected
- **WHEN** a user asks Ruby to open an app not present in the configured allowlist
- **THEN** Ruby does not run the `open` command and returns an unsupported app message

### Requirement: Shell execution pathway remains disabled in v1
The system SHALL include command policy scaffolding with allowlist and denylist definitions, SHALL keep shell execution disabled by default, and MUST NOT expose arbitrary shell execution to LLM tool calls.

#### Scenario: Dangerous shell request is refused
- **WHEN** a request asks Ruby to run a prohibited command such as `rm -rf` or `sudo`
- **THEN** Ruby refuses execution and states that shell command execution is not supported in v1
