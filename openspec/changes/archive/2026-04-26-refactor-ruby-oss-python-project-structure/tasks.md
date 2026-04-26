## 1. Package and entrypoint restructuring

- [x] 1.1 Create `ruby/` package layout (`core`, `config`, `audio`, `providers`, `tools`, `security`, `setup`) with `__init__.py` files.
- [x] 1.2 Move current assistant runtime logic from root modules into package modules while preserving behavior.
- [x] 1.3 Replace root `app.py` with thin runner that imports and executes `ruby.cli.main`.
- [x] 1.4 Add `ruby/__main__.py` to support `python -m ruby` execution.

## 2. CLI command surface

- [x] 2.1 Implement `ruby/cli.py` command routing for `init`, `run`, `doctor`, `models`, and `config`.
- [x] 2.2 Set default CLI behavior to `run` when no command is provided.
- [x] 2.3 Verify command parity for `python app.py <cmd>` and `python -m ruby <cmd>` for required commands.

## 3. Configuration and runtime directory policy

- [x] 3.1 Implement `ruby/config/settings.py` with `config.json` -> `config.example.json` fallback and root path resolution helpers.
- [x] 3.2 Add optional `.env` loading via `python-dotenv` without logging raw secret values.
- [x] 3.3 Create tracked `config.example.json` and `.env.example` defaults for OSS onboarding.
- [x] 3.4 Ensure runtime folders (`recordings`, `responses`, `ruby_workspace`, `whisper.cpp`) are created automatically when missing.

## 4. Provider and assistant abstraction refactor

- [x] 4.1 Add provider base contracts for STT, LLM, and TTS under `ruby/providers/*/base.py`.
- [x] 4.2 Move Whisper, Ollama, and Kokoro implementations into `whisper_cpp.py`, `ollama.py`, and `kokoro.py` modules.
- [x] 4.3 Add disabled OpenRouter placeholder provider that reads `OPENROUTER_API_KEY` and raises a clear setup error if missing.
- [x] 4.4 Implement `ruby/core/schemas.py` dataclasses (`AssistantResponse`, `ToolResult`) and wire them into assistant flow.
- [x] 4.5 Implement `ruby/core/assistant.py` `RubyAssistant` orchestration with `handle_text` and `handle_audio` methods.

## 5. Audio and setup domain extraction

- [x] 5.1 Move recording, playback, and wake-word logic into `ruby/audio/recorder.py`, `ruby/audio/player.py`, and `ruby/audio/wake.py`.
- [x] 5.2 Keep playback behavior aligned with existing macOS `afplay` execution.
- [x] 5.3 Move setup/init/model checks into `ruby/setup/init_wizard.py`, `ruby/setup/model_discovery.py`, and `ruby/setup/doctor.py`.
- [x] 5.4 Implement doctor checks for dependencies, config, whisper.cpp assets, models, runtime folders, and provider connectivity expectations.

## 6. Tool safety, registry, and sandboxing

- [x] 6.1 Implement `ruby/tools/registry.py` with registration, enablement checks, and guarded invocation behavior.
- [x] 6.2 Move `get_time` and `open_app` into `ruby/tools/system.py` and file tools into `ruby/tools/files.py`.
- [x] 6.3 Implement `ruby/security/paths.py` `safe_resolve_workspace_path(workspace_dir, requested_path)` with traversal and unsafe path blocking.
- [x] 6.4 Add `ruby/security/command_policy.py` structure to keep command restrictions explicit and centralized.

## 7. Repository hygiene and contributor UX

- [x] 7.1 Update `.gitignore` to ignore local runtime/config/secrets artifacts and keep OSS artifacts tracked.
- [x] 7.2 Clean `requirements.txt` to the approved dependency set and include `pytest`.
- [x] 7.3 Add `scripts/setup_dev.sh` venv bootstrap script and run doctor as a final check.
- [x] 7.4 Ensure LICENSE exists (MIT placeholder with `Copyright (c) 2026 4WRN Online`).

## 8. Tests and documentation

- [x] 8.1 Add pytest coverage for config fallback behavior, workspace path traversal blocking, registry unknown-tool rejection, and enabled-tool success path.
- [x] 8.2 Rewrite `README.md` with OSS framing, quick start, CLI commands, architecture summary, security model, providers, and git workflow.
- [x] 8.3 Create `docs/architecture.md`, `docs/security.md`, and `docs/providers.md` aligned with new package architecture.
- [x] 8.4 Validate required runtime commands still work: `python app.py run`, `python app.py init`, `python app.py doctor`, `python -m ruby run`.

## 9. Final verification and commit

- [x] 9.1 Run test and command smoke verification before finalizing.
- [x] 9.2 Inspect `git status` to confirm expected file changes.
- [ ] 9.3 Commit with message `Refactor Ruby into OSS project structure` and do not push.
