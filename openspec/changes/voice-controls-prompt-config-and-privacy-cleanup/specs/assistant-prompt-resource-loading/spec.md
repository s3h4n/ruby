## ADDED Requirements

### Requirement: Runtime system prompt is loaded from prompt resource file
The runtime pipeline SHALL load the assistant system prompt from `prompts/system_prompt.md` instead of hardcoding assistant identity text in Python source.

#### Scenario: Prompt file is present
- **WHEN** the runtime pipeline initializes assistant prompt content
- **THEN** it reads `prompts/system_prompt.md` and uses that content for system prompt messages

### Requirement: Missing prompt resource yields clear developer-facing error
If `prompts/system_prompt.md` is missing or unreadable, the system MUST fail with a clear developer-facing error that identifies the missing prompt resource.

#### Scenario: Prompt file missing
- **WHEN** prompt loading is attempted and `prompts/system_prompt.md` does not exist
- **THEN** initialization fails with an explicit prompt-file configuration error instead of a generic traceback

### Requirement: Prompt behavior remains provider-reusable
Prompt-loading behavior SHALL be provider-agnostic so the same prompt resource can be reused by future model providers without changing prompt text location.

#### Scenario: Message formatting still owned by pipeline
- **WHEN** prompt loading is integrated into `pipeline.py`
- **THEN** `pipeline.py` keeps message formatting responsibilities while assistant identity text remains outside Python source
