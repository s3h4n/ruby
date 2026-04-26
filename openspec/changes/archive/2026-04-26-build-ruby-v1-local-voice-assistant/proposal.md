## Why

Ruby needs a working v1 that runs fully on-device while keeping a clean architecture for future growth. This change establishes a local-first voice assistant that is safe by default today and provider-ready for future cloud, API, and UI extensions without rewriting core logic.

## What Changes

- Create a modular `ruby/` package with clear boundaries for core orchestration, providers, audio, tools, security, and interfaces.
- Implement a local voice flow: wake handling -> record command -> whisper.cpp transcription -> Ollama response -> optional safe tool execution -> Kokoro speech output.
- Add provider abstractions (`STTProvider`, `LLMProvider`, `TTSProvider`) and local v1 implementations (`WhisperCppSTTProvider`, `OllamaLLMProvider`, `KokoroTTSProvider`).
- Add a central tool registry with metadata (name, description, args, risk level, enabled flag) and ship safe v1 tools only: `get_time`, `open_app`, `list_directory`, `create_folder`, `create_file`.
- Add security guardrails: workspace-only file operations in `ruby_workspace/`, no delete tools in v1, and shell execution disabled by default with allowlist/denylist policy scaffolding.
- Add startup validation checks (config, folders, whisper paths, Ollama reachability, Kokoro import, microphone readiness) with actionable troubleshooting guidance.
- Add a complete `README.md` covering setup, runtime behavior, safety model, and extension paths for future providers, search, tools, and interfaces.

## Capabilities

### New Capabilities
- `assistant-runtime-core`: Core assistant pipeline, schemas, errors, and response handling with text/audio entrypoints.
- `provider-abstraction-layer`: Pluggable STT/LLM/TTS provider contracts with local implementations and config-driven selection.
- `voice-cli-interface`: Voice-oriented CLI runtime with wake flow, recording, playback, and root runner integration.
- `tool-safety-and-workspace-ops`: Tool registry, safe local tools, workspace sandbox enforcement, and command/file policy controls.
- `startup-validation-and-ops`: Startup health checks, local dependency verification, and operator-facing troubleshooting behavior.

### Modified Capabilities
- None.

## Impact

- Adds a new production code package layout under `ruby/` and root `app.py` runner wiring.
- Introduces/updates configuration contract in `config.json` for assistant mode, providers, audio settings, security controls, and tool allowlists.
- Creates runtime folders (`recordings/`, `responses/`, `ruby_workspace/`) and enforces sandboxed file operations.
- Defines v1-local-only behavior while preserving extension seams for future cloud providers, search/web tooling, safe shell tooling, web UI, and API server interfaces.
