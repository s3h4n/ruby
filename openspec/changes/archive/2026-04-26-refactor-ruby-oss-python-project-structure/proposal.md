## Why

The repository currently behaves as a working local voice assistant but is organized as a hobby codebase rather than a maintainable open-source Python project. This change is needed now to establish a clean package layout, explicit runtime boundaries, and contributor-ready documentation without changing core behavior.

## What Changes

- Reorganize source code into a structured `ruby/` package with clear domains (`core`, `audio`, `providers`, `tools`, `security`, `setup`, `config`) while keeping behavior compatible.
- Define a stable CLI entry surface (`app.py` thin runner, `python -m ruby`, and command routing for `init`, `run`, `doctor`, `models`, `config`).
- Introduce configuration loading and path resolution via centralized settings modules and adopt OSS-safe config conventions (`config.example.json` tracked, `config.json` ignored).
- Add provider abstractions and move existing Whisper/Ollama/Kokoro implementations into dedicated provider modules; include OpenRouter as a disabled placeholder.
- Add sandboxed tool execution and path security guarantees for workspace operations.
- Add baseline tests, docs, development bootstrap script, and repository hygiene updates (`.gitignore`, `requirements.txt`, README, LICENSE).

## Capabilities

### New Capabilities
- `project-structure-and-cli`: Defines the package layout, runtime command entry points, and command behavior compatibility.
- `configuration-and-runtime-layout`: Defines settings loading behavior, config/env handling, and required runtime directories.
- `provider-and-assistant-abstractions`: Defines assistant core contracts and STT/LLM/TTS provider interfaces and module responsibilities.
- `tool-registry-and-workspace-sandbox`: Defines tool registration/enablement behavior and enforced workspace path safety.
- `operational-readiness-and-docs`: Defines doctor/models checks, OSS documentation expectations, and baseline test coverage.

### Modified Capabilities
- None.

## Impact

- Affects most runtime Python modules by relocating logic into `ruby/` package namespaces.
- Adds and updates root project artifacts (`README.md`, `requirements.txt`, `.gitignore`, `LICENSE`, `app.py`, examples/docs/tests/scripts).
- No external API contract changes are expected; command surface remains functionally compatible while becoming better structured.
