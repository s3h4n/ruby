# Architecture

Ruby is a local-first assistant with a package-first Python layout under `ruby/`.

## Runtime Flow

1. CLI entrypoint dispatches `run`, `init`, `doctor`, `models`, or `config`.
2. `ruby.app.build_app_context()` loads settings, creates runtime directories, and runs startup checks.
3. `RubyAssistant` coordinates providers and tool registry for text/audio requests.
4. Audio mode records input, transcribes via STT, routes to LLM/tool flow, then synthesizes playback output.

## Package Layout

- `ruby/cli.py` and `ruby/__main__.py`: command routing and module execution.
- `ruby/core/`: assistant orchestration, typed response/tool schemas, shared errors.
- `ruby/config/`: typed settings model, config fallback, and `.env` loading.
- `ruby/audio/`: recorder/player/wake-word domain.
- `ruby/providers/`: provider contracts and concrete STT/LLM/TTS implementations.
- `ruby/tools/`: system and workspace tool handlers plus registry.
- `ruby/security/`: path sandboxing, command policy, and risk permission checks.
- `ruby/setup/`: init wizard, model discovery, and doctor diagnostics.

## Entry Point Parity

Both command forms are supported and expected to behave the same:

- `python app.py <command>`
- `python -m ruby <command>`

When no command is provided, both forms default to `run`.
