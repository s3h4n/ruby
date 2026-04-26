## ADDED Requirements

### Requirement: Source code is organized as a Python package
The project SHALL place assistant source code under a top-level `ruby/` package with domain subpackages for `core`, `config`, `audio`, `providers`, `tools`, `security`, and `setup`.

#### Scenario: Required package paths exist
- **WHEN** a contributor inspects the repository tree
- **THEN** the `ruby/` package and required domain subpackages are present with importable `__init__.py` files

### Requirement: Root app runner remains a thin compatibility entry point
The root `app.py` SHALL only delegate execution to `ruby.cli.main` and SHALL NOT contain assistant business logic.

#### Scenario: app.py delegates to CLI
- **WHEN** `python app.py` is executed
- **THEN** command dispatch is handled by `ruby.cli.main`

### Requirement: Module execution supports the same command surface
The package SHALL expose `ruby/__main__.py` so that `python -m ruby` supports `init`, `run`, `doctor`, `models`, and `config`, defaulting to `run` when no command is provided.

#### Scenario: Default command routing
- **WHEN** a user runs `python -m ruby` with no subcommand
- **THEN** the assistant starts the same run flow used by `python app.py run`
