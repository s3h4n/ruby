## ADDED Requirements

### Requirement: Startup health checks must validate core local dependencies
On startup, Ruby SHALL validate config presence, required directories, whisper CLI path, whisper model path, Ollama API reachability, Kokoro import availability, and microphone access readiness.

#### Scenario: Missing dependency fails fast with guidance
- **WHEN** any required dependency check fails during startup
- **THEN** Ruby exits or pauses startup with a clear, actionable remediation message for that specific failure

### Requirement: Runtime directories must be ensured automatically
Ruby SHALL create required runtime directories if missing, including `recordings/`, `responses/`, and configured workspace directory.

#### Scenario: First run creates missing runtime folders
- **WHEN** Ruby starts in a clean project folder without required runtime directories
- **THEN** Ruby creates missing directories before entering assistant runtime

### Requirement: Configuration must express local-first provider-ready settings
The project SHALL maintain a structured `config.json` containing assistant, provider, audio, security, and tool sections with defaults aligned to local v1 behavior.

#### Scenario: Default configuration enforces local-only v1
- **WHEN** Ruby runs with the default checked-in config
- **THEN** only local providers are active, shell execution is disabled, and approved v1 tools are enabled

### Requirement: Operator documentation must cover setup, safety, and extension paths
The repository README SHALL document v1 capabilities, setup steps, safety boundaries, troubleshooting, and how to add future providers and interfaces without changing core architecture.

#### Scenario: New developer can run Ruby from docs
- **WHEN** a developer follows README setup and run instructions on macOS
- **THEN** they can launch Ruby and understand current guardrails plus planned extension approach
