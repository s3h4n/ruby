# Ruby

Ruby is an open-source, local-first assistant for macOS with a command-based CLI.

It supports voice and text interaction, local model integration, and guarded tool execution inside a workspace sandbox.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
cp .env.example .env
python app.py init
python app.py doctor
python app.py run
```

## CLI Commands

Both entrypoints are supported:

- `python app.py <command>`
- `python -m ruby <command>`

Available commands:

- `run` (default): start runtime assistant loop
- `init`: bootstrap local setup and config
- `doctor`: run diagnostics and remediation hints
- `models`: list discovered Whisper/Ollama models
- `config`: print safe configuration and env status

## Configuration

- Primary local config: `config.json` (gitignored)
- Fallback template: `config.example.json` (tracked)
- Secrets source: `.env` (gitignored)
- Secrets template: `.env.example` (tracked)

The runtime will fall back to `config.example.json` when `config.json` is absent.

## Runtime Directories

Ruby creates missing runtime directories automatically:

- `recordings/`
- `responses/`
- `ruby_workspace/`
- `whisper.cpp/`

## Architecture Summary

Core package structure lives in `ruby/`:

- `ruby/cli.py`, `ruby/__main__.py`: command routing and module execution
- `ruby/core/`: assistant flow and typed schemas
- `ruby/config/`: settings model and config/env loading
- `ruby/audio/`: recorder, playback, wake-word logic
- `ruby/providers/`: STT/LLM/TTS contracts and implementations
- `ruby/tools/`: system/file tool handlers and registry
- `ruby/security/`: path sandbox and command policy
- `ruby/setup/`: init wizard, model discovery, diagnostics

Additional docs:

- `docs/architecture.md`
- `docs/security.md`
- `docs/providers.md`

## Security Model

- Workspace-only file operations (`ruby_workspace/`)
- Path traversal and unsafe path forms blocked
- Unknown or disabled tools rejected by registry
- Shell tool disabled by default
- Confirmation gating for medium/high-risk tools

## Providers

- STT: Whisper.cpp (`whisper_cpp`)
- LLM: Ollama (`ollama`)
- LLM placeholder: OpenRouter (`openrouter`) with required `OPENROUTER_API_KEY`
- TTS: Kokoro (`kokoro`)

## Development

Use the bootstrap script:

```bash
./scripts/setup_dev.sh
```

Run tests:

```bash
python3 -m pytest -q
```

## Git Workflow

- Keep changes scoped and reviewable
- Run tests before committing
- Use focused commits and open PRs for review
