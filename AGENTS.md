# AGENTS Notes

## Quick Reality Check
- This is a Python repo (not Ruby language). Runtime code is under `ruby/`.
- Canonical CLI entrypoints must stay behaviorally identical: `python app.py <command>` and `python -m ruby <command>`.
- Command routing lives in `ruby/interfaces/cli.py`; `app.py` and `ruby/cli.py` are thin delegators.

## Verified Dev Commands
- Setup: `./scripts/setup_dev.sh` (creates `.venv`, installs `requirements.txt`, runs `python3 app.py doctor`).
- Run tests: `python -m pytest -q`.
- Run one test: `python -m pytest tests/test_cli_runtime_commands.py::test_slash_commands_are_handled_locally_without_llm_calls -q`.
- Run app: `python app.py run` (or `python -m ruby run`).
- Diagnostics: `python app.py doctor`, `python app.py models`, `python app.py config`.

## Runtime Prerequisites Enforced at Startup
- `whisper-cli` must exist and execute (`providers.stt.whisper_cli`).
- Whisper model file must exist (`providers.stt.model`).
- Ollama must be reachable (startup probes `/api/tags`; config defaults to `http://localhost:11434/api/chat`).
- `kokoro` must be importable in active venv.
- Microphone permission/access is checked before runtime starts.

## Config And Secrets Gotchas
- `config.json` is local-only and gitignored; fallback is `config.example.json` when `config.json` is missing.
- `load_settings()` auto-migrates missing defaults into `config.json` when using the primary config file.
- Do not add inline secret fields in config (`api_key`, `token`, `secret`, `password`): config load rejects them.
- Keep new config fields mirrored in both `DEFAULT_CONFIG` (`ruby/config/settings.py`) and `config.example.json`.
- Type checks are strict for some fields: `debug` must be boolean; `conversation.max_turns` must be positive int.

## Architecture Pointers That Matter
- App assembly/startup checks/tool registry: `ruby/app.py`.
- Assistant orchestration and conversation memory: `ruby/core/assistant.py`, `ruby/core/conversation.py`.
- Provider factory and allowed provider names: `ruby/providers/factory.py`.
- TTS compatibility shim exists: import path `ruby.providers.tts.kokoro` re-exports implementation from `ruby/providers/tts/kokoro_tts.py`.

## Testing Conventions
- Tests are mixed `pytest` + `unittest` style; run all via `python -m pytest`.
- CLI parity and return-code behavior are contract-tested (`tests/test_cli_entrypoints.py`, `tests/test_command_dispatch.py`).
- Config migration/hygiene behavior is heavily tested; update tests whenever config schema changes.

## OpenSpec Workflow In This Repo
- Custom slash-command specs live in `.opencode/command/` (`opsx-propose`, `opsx-apply`, `opsx-archive`, `opsx-explore`).
- OpenSpec project config is `openspec/config.yaml` (schema: `spec-driven`).
- Active changes are under `openspec/changes/`; archived changes are under `openspec/changes/archive/`.
