## ADDED Requirements

### Requirement: Interactive init bootstraps first-run configuration
The system SHALL provide an interactive `python app.py init` flow that detects local prerequisites, collects model selections, and writes `config.json` with non-secret values only.

#### Scenario: Init creates config from selected local models
- **WHEN** a user runs `python app.py init` and whisper/Ollama models are discoverable
- **THEN** the wizard SHALL present selectable model menus and persist selected model values to `config.json`

### Requirement: Init SHALL bootstrap environment files safely
The system SHALL create `.env` from `.env.example` if `.env` does not exist and SHALL not write provider API keys into `config.json`.

#### Scenario: Missing .env is generated from template
- **WHEN** `.env` is missing and user completes init
- **THEN** `.env` SHALL be created from `.env.example` and `config.json` SHALL remain secret-free

### Requirement: Whisper model download is controlled and allowlisted
If no whisper model exists, init SHALL offer an allowlisted model download flow using `download-ggml-model.sh` with safe subprocess execution.

#### Scenario: No local whisper models found
- **WHEN** init detects zero `ggml-*.bin` files
- **THEN** init SHALL offer allowlisted model choices and re-scan model list after successful download
