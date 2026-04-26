## ADDED Requirements

### Requirement: Setup and diagnostics commands are modularized
The setup domain SHALL provide `init_wizard`, `model_discovery`, and `doctor` modules, and CLI commands SHALL delegate setup and diagnostics behavior through these modules.

#### Scenario: Doctor command validates runtime prerequisites
- **WHEN** `python app.py doctor` is executed
- **THEN** checks include config availability, whisper.cpp artifacts, selected model availability, required runtime folders, and key Python package availability

### Requirement: Models command reports discovered and selected models
The models command SHALL display discovered Whisper models, discovered Ollama models, and currently selected model identifiers from configuration.

#### Scenario: Model inventory output includes configured selections
- **WHEN** `python app.py models` is executed
- **THEN** output includes both discovered model lists and configured selected models

### Requirement: Baseline tests cover critical safety and dispatch behavior
The repository SHALL include pytest-based tests for config fallback loading, workspace path traversal blocking, registry unknown-tool rejection, and enabled-tool execution.

#### Scenario: Safety tests fail on insecure behavior
- **WHEN** path sandbox or registry guardrails are removed or bypassed
- **THEN** baseline tests fail and signal regression

### Requirement: OSS-facing docs and bootstrap assets are present
The repository SHALL include updated README guidance, architecture/security/provider docs, cleaned requirements, `.env.example`, `config.example.json`, and `scripts/setup_dev.sh` for contributor onboarding.

#### Scenario: Fresh contributor setup path is documented and executable
- **WHEN** a contributor follows documented quick-start and dev setup steps
- **THEN** they can create a virtual environment, install dependencies, and run diagnostics without undocumented steps
