## Why

Ruby's voice loop is functional, but key maintainability and operator-control gaps increase implementation risk for the next iterations. Assistant identity is hardcoded in `pipeline.py`, interruption is incomplete across long-running stages, and local machine paths leak through Whisper-related configuration and output.

## What Changes

- Move the assistant system prompt into `prompts/system_prompt.md` and load it from runtime code with a clear developer-facing missing-file error.
- Keep `pipeline.py` focused on message formatting/orchestration so the same prompt asset can be reused by future model providers.
- Add Enter-key toggle control for recording (`start` on first Enter, `stop and send` on second Enter) while retaining timeout auto-stop as fallback.
- Add interruption support (`Esc`/`Ctrl+C`) that safely cancels recording, transcription, thinking, or speaking and always returns the CLI to `[Ready]` with clean `[Interrupted]` output.
- Add shared cancellation signaling across long-running stages so canceled work is halted or ignored and cannot leak into later states.
- Remove hardcoded/local-path exposure in Whisper and related audio/config/logging paths, introduce safe env-based configuration where needed, and improve `.gitignore` for local/sensitive artifacts.
- Add `.env.example` placeholders for machine-specific config and keep user-facing errors clean without raw stack traces/private path leakage.

## Capabilities

### New Capabilities
- `assistant-prompt-resource-loading`: Externalize assistant identity/system prompt into a reusable prompt file and load it at runtime with explicit developer diagnostics.
- `interactive-voice-control-and-interruption`: Add Enter toggle recording control and cross-stage user interruption that returns safely to `[Ready]`.
- `cancellation-aware-voice-pipeline`: Enforce shared cancellation handling for recording, transcription, model generation, and TTS playback.
- `privacy-safe-local-config-and-output`: Remove local path leakage, adopt safe env/config patterns, and keep normal CLI output free of private machine details.

### Modified Capabilities
- None.

## Impact

- Affected runtime orchestration in the voice/LLM pipeline (including `pipeline.py`) and stage transition handling.
- New prompt asset under `prompts/` and config/environment loading updates for local path management.
- Input handling updates for Enter toggle and interruption behavior in CLI runtime flow.
- Security/privacy hygiene updates in logging/error surfaces and repository ignore rules (`.gitignore`, `.env.example`, local artifact exclusions).
