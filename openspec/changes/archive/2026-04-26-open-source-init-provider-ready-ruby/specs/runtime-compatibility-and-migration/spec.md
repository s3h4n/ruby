## ADDED Requirements

### Requirement: Existing default invocation SHALL remain functional
The system SHALL keep `python app.py` behavior equivalent to `python app.py run` for existing users.

#### Scenario: Existing user upgrades and runs legacy command
- **WHEN** user executes `python app.py` after upgrading
- **THEN** Ruby SHALL enter normal runtime flow without requiring command changes

### Requirement: Legacy configuration mismatches SHALL produce migration guidance
When existing config lacks required fields for new command/provider workflows, runtime SHALL either apply deterministic migration or emit explicit init guidance.

#### Scenario: Missing new config keys
- **WHEN** startup detects missing required config sections introduced by this change
- **THEN** Ruby SHALL print clear migration guidance, including `python app.py init`, instead of opaque tracebacks

### Requirement: Migration flow SHALL preserve local-first defaults
Compatibility handling SHALL preserve local provider defaults unless user explicitly changes providers/models.

#### Scenario: Existing local config can be upgraded safely
- **WHEN** migration succeeds
- **THEN** resulting config SHALL keep local-first provider values and remain secret-free
