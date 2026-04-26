## Why

Ruby's current CLI interaction feels opaque and stateless, which makes voice testing slow and follow-up prompts unreliable. Improving pipeline visibility, mixed voice/text input, and session memory now will make the backend trustworthy and testable before frontend work begins.

## What Changes

- Add explicit pipeline state feedback for voice requests: Ready, Recording, Recorded, Transcribing, Transcript ready, Thinking, Response ready, Speaking, and Done.
- Update push-to-talk behavior to support Enter-triggered recording and direct typed input at the same prompt.
- Add slash commands (`/help`, `/history`, `/clear`, `/status`, `/quit`) handled in CLI without sending to the LLM.
- Introduce in-session conversation memory with turn trimming via new conversation config (`enabled`, `max_turns`) and a dedicated conversation manager.
- Refactor LLM request path to pass full chat message arrays (system + history + latest user message) to Ollama `/api/chat` with `stream=false`.
- Improve user-facing error handling for microphone, STT, LLM, and TTS failures and keep CLI alive for recovery.
- Add optional debug mode to gate internal logs and raw provider details behind configuration.
- Preserve existing providers/models and avoid frontend/web stack changes in this scope.

## Capabilities

### New Capabilities

- `cli-backend-conversation-ux`: Defines stateful CLI interaction behavior, unified voice/text input handling, session conversation memory, slash commands, and resilient backend status/error reporting.

### Modified Capabilities

None.

## Impact

- Affected code: CLI interaction loop, orchestration pipeline between recording/STT/LLM/TTS, provider integration points, and configuration loading/validation.
- APIs: Ollama chat request payload moves to full message history format.
- Dependencies: No new runtime framework dependencies required; remain on existing whisper.cpp, Ollama, and Kokoro stack.
- Systems: Improves local development/test feedback loop and establishes backend interaction contract for future frontend integration.
