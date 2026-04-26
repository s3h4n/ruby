## ADDED Requirements

### Requirement: Model discovery SHALL provide deterministic local results
The system SHALL discover whisper models from configured model directories and Ollama models from local Ollama tags API responses.

#### Scenario: Models command lists available runtimes
- **WHEN** a user runs `python app.py models`
- **THEN** output SHALL list discovered whisper model files and available Ollama model tags

### Requirement: Doctor SHALL run full health checks with remediation
The system SHALL implement a `doctor` command that checks binary/runtime availability and prints actionable remediation text for failures.

#### Scenario: Doctor identifies missing dependency
- **WHEN** whisper binary is missing or non-runnable
- **THEN** doctor SHALL print a failed check plus a concrete rebuild/fix command suggestion

### Requirement: Ollama model discovery SHALL use requests client
Ollama model discovery and checks SHALL use `requests` against local Ollama API endpoints with timeout handling.

#### Scenario: Ollama API is unreachable
- **WHEN** local Ollama endpoint cannot be reached
- **THEN** doctor SHALL report failure and suggest starting Ollama service
