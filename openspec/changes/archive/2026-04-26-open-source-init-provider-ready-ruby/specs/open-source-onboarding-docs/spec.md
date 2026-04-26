## ADDED Requirements

### Requirement: README SHALL document open-source quickstart and commands
Documentation SHALL include setup prerequisites, `init` first-run flow, command usage (`run`, `doctor`, `models`, `config`), and troubleshooting guidance.

#### Scenario: New contributor follows quickstart
- **WHEN** a fresh user reads README and executes listed setup steps
- **THEN** they SHALL be able to initialize and run Ruby without hidden steps

### Requirement: Repository hygiene files SHALL support secure onboarding defaults
The project SHALL include `.env.example` template and `.gitignore` entries for `.env`, runtime artifacts, and Python caches while keeping `config.json` tracked.

#### Scenario: User initializes repo locally
- **WHEN** user runs init and creates local runtime artifacts
- **THEN** sensitive/local-only files SHALL remain untracked according to `.gitignore`
