## 1. CLI Command Dispatcher and Backward Compatibility

- [ ] 1.1 Add command parsing to `app.py` for `init`, `run`, `doctor`, `models`, and `config`
- [ ] 1.2 Keep no-argument invocation mapped to `run` behavior (`python app.py` -> `python app.py run`)
- [ ] 1.3 Refactor CLI entrypoints in `ruby/interfaces/cli.py` to expose command handlers
- [ ] 1.4 Add clear command-level help text for unknown commands
- [ ] 1.5 Add tests covering command dispatch and default run compatibility

## 2. Init Wizard and First-Run Bootstrap

- [ ] 2.1 Create `ruby/setup/init_wizard.py` with step-driven interactive wizard orchestration
- [ ] 2.2 Implement whisper.cpp binary detection from configured/default candidate paths
- [ ] 2.3 Implement whisper model discovery (`ggml-*.bin`) and selection prompt
- [ ] 2.4 Integrate optional allowlisted whisper model download flow via `download-ggml-model.sh`
- [ ] 2.5 Implement Ollama model discovery and selection prompt
- [ ] 2.6 Integrate optional Ollama pull flow using safe non-shell subprocess invocation
- [ ] 2.7 Generate or update `config.json` with selected non-secret values only
- [ ] 2.8 Create required runtime folders (`recordings`, `responses`, `ruby_workspace`) during init
- [ ] 2.9 Add init-flow tests for discovery, selection persistence, and missing-model handling

## 3. Environment and Dependency Hygiene

- [ ] 3.1 Add `python-dotenv` dependency and load env on startup/init paths
- [ ] 3.2 Ensure `requests` is used for Ollama tags API queries in discovery/doctor modules
- [ ] 3.3 Add `.env.example` with documented key placeholders and safe defaults
- [ ] 3.4 Add `.env` bootstrap-from-template logic when missing
- [ ] 3.5 Ensure `config.json` remains non-secret and excludes API keys
- [ ] 3.6 Add tests that verify secrets are read from env and not printed in config output

## 4. Provider-Ready Architecture and OpenRouter Placeholder

- [ ] 4.1 Refine provider interfaces and factory paths for STT/LLM/TTS selection from config/env
- [ ] 4.2 Keep local defaults (`whisper_cpp`, `ollama`, `kokoro`) operational after refactor
- [ ] 4.3 Add `ruby/providers/llm/openrouter.py` placeholder implementation disabled by default
- [ ] 4.4 Ensure OpenRouter implementation reads key from env and never logs key material
- [ ] 4.5 Add provider selection tests for local defaults and non-selected OpenRouter inactivity

## 5. Model Discovery and Doctor Diagnostics

- [ ] 5.1 Create `ruby/setup/model_discovery.py` for whisper and Ollama model listing
- [ ] 5.2 Add `python app.py models` command output showing discovered whisper/Ollama models
- [ ] 5.3 Create `ruby/setup/doctor.py` health checks for config/env, binaries, models, Ollama reachability, Kokoro import, and microphone
- [ ] 5.4 Ensure doctor prints pass/fail lines with concrete remediation guidance
- [ ] 5.5 Add tests for doctor failure output (missing whisper binary/model, unreachable Ollama, missing Kokoro)

## 6. Security Guardrails and Safe Subprocess Usage

- [ ] 6.1 Enforce allowlisted subprocess argument arrays for download/pull operations (no shell strings)
- [ ] 6.2 Preserve workspace-only file tooling and path traversal protections
- [ ] 6.3 Keep shell execution disabled by default and retain denylist policy scaffolding
- [ ] 6.4 Verify dangerous operations are refused in runtime and tooling paths
- [ ] 6.5 Add/extend tests for traversal blocking, unknown app rejection, and command safety constraints

## 7. Runtime Compatibility and Migration Guidance

- [ ] 7.1 Implement config compatibility checks for new required fields
- [ ] 7.2 Add deterministic migration where feasible for older config structure
- [ ] 7.3 Add explicit fallback guidance (`python app.py init`) when migration cannot be applied safely
- [ ] 7.4 Add tests for legacy config detection and guidance output

## 8. Documentation and Repository Updates

- [ ] 8.1 Update `.gitignore` to include `.env`, runtime artifacts, and Python cache outputs while keeping `config.json` tracked
- [ ] 8.2 Rewrite README with open-source quickstart (`init` then `run`) and command reference (`run`, `doctor`, `models`, `config`)
- [ ] 8.3 Document model switching and provider extension workflow for contributors
- [ ] 8.4 Document security model and secret-handling rules clearly
- [ ] 8.5 Run end-to-end verification flow (`init`, `models`, `doctor`, `run`) and record observed behavior
