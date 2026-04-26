## Why

Ruby currently assumes fixed local model configuration, which makes onboarding hard for open-source users and brittle across different machines. We need a first-run setup and diagnostics flow so users can clone, initialize, choose local models, and run safely while keeping a clean path to future cloud providers.

## What Changes

- Add command-based CLI entrypoints: `init`, `run`, `doctor`, `models`, and `config` (default to `run`).
- Add interactive first-run init wizard that detects whisper.cpp, discovers/downloads whisper models, discovers Ollama models, and writes `config.json` from selections.
- Add environment file flow: create `.env.example`, create `.env` from template when missing, load env vars via `python-dotenv`, and keep secrets out of `config.json`.
- Refactor provider layer to be provider-ready with explicit STT/LLM/TTS interfaces and implementations for `whisper_cpp`, `ollama`, `kokoro`, plus disabled `openrouter` placeholder.
- Add model discovery and health checks (`doctor`) for whisper runtime, selected model existence, Ollama availability/model presence, Kokoro import, and mic readiness.
- Keep security posture strict for open-source use: workspace-only file tools, traversal blocking, no dangerous shell execution, no secret logging.
- Update docs and repository hygiene (`requirements.txt`, `.gitignore`, README quick start and command documentation).

## Capabilities

### New Capabilities
- `first-run-init-and-config-bootstrap`: interactive init flow to discover/select models, bootstrap config/env, and create runtime folders.
- `multi-command-cli-runtime`: command dispatcher with `init`, `run`, `doctor`, `models`, and `config` behavior and backwards-compatible default run path.
- `provider-ready-local-runtime`: provider abstraction and selection for STT/LLM/TTS with local-first defaults and future cloud-ready extension points.
- `model-discovery-and-health-diagnostics`: whisper/Ollama model discovery and doctor diagnostics with actionable pass/fail remediation.
- `open-source-security-and-secrets-hygiene`: enforce workspace sandboxing, command safety constraints, secret separation, and non-secret config output.
- `open-source-onboarding-docs`: setup/run/model-switch/security documentation for new contributors and users.
- `runtime-compatibility-and-migration`: preserve default run behavior and handle legacy config via migration or explicit init guidance.

### Modified Capabilities
- None.

## Impact

- Affected code: `app.py`, CLI interface modules, config loading, provider modules, setup/doctor/model discovery modules, README, `.gitignore`, dependency files.
- New dependencies: `python-dotenv`, `requests` for Ollama model discovery.
- New/updated artifacts: `config.json`, `.env.example`, optional `.env` generation flow, setup modules under `ruby/setup/`.
- User impact: fresh users can run `python app.py init` then `python app.py run`; existing users gain `models`, `config`, and `doctor` without losing current run path.
