## ADDED Requirements

### Requirement: Runtime must not hardcode absolute local machine paths
Ruby SHALL avoid hardcoded absolute local paths for Whisper models, audio artifacts, transcripts, and temporary runtime files.

#### Scenario: Path configuration resolution
- **WHEN** runtime resolves local file paths for Whisper and voice artifacts
- **THEN** it uses project-relative paths and/or environment-configured values rather than embedded machine-specific absolute paths

### Requirement: User-facing output must not expose private local paths
Normal CLI output MUST NOT display private local machine paths, usernames, or home-directory details in expected error and interruption flows.

#### Scenario: Missing Whisper model file
- **WHEN** the Whisper model is unavailable at configured location
- **THEN** CLI output shows a sanitized user-facing error message without printing the private absolute path

### Requirement: Safe local configuration pattern is documented
The repository MUST provide a safe local configuration template via `.env.example` for required machine-specific values, and `.env` files MUST remain uncommitted.

#### Scenario: Local environment setup
- **WHEN** a developer configures local runtime paths
- **THEN** they can use documented env keys from `.env.example`, and missing required values produce clear developer-facing configuration guidance

### Requirement: Generated local-sensitive artifacts are git-ignored
Repository ignore rules SHALL exclude local-sensitive generated files such as env files, local recordings, temporary audio files, transcripts, and cache artifacts relevant to this project.

#### Scenario: Git status after local run
- **WHEN** Ruby generates local voice artifacts during development
- **THEN** those generated local files are excluded from version control by `.gitignore`
