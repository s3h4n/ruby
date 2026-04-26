## 1. Configuration and session state foundations

- [x] 1.1 Add `conversation.enabled`, `conversation.max_turns`, and `debug` fields to runtime configuration with safe defaults.
- [x] 1.2 Validate and normalize conversation/debug config at startup so invalid values fail fast with clear errors.
- [x] 1.3 Create `ruby/core/conversation.py` with `add_user_message`, `add_assistant_message`, `get_messages`, and `clear` methods.
- [x] 1.4 Add turn-trimming logic so only the latest configured user-assistant turns are retained in memory.

## 2. LLM message-history integration

- [x] 2.1 Refactor the LLM provider interface to accept role-based `messages` arrays instead of single-message input.
- [x] 2.2 Update Ollama `/api/chat` request construction to send full message history with `stream=false`.
- [x] 2.3 Ensure assistant replies stored in history are human-readable text suitable for follow-up context and `/history` display.
- [x] 2.4 Preserve current model/provider selection behavior while wiring message-history requests.

## 3. CLI interaction and command routing

- [x] 3.1 Update the main prompt flow to support empty input (voice), typed text (chat), and slash command handling in one loop.
- [x] 3.2 Implement `/help`, `/history`, `/clear`, `/status`, and `/quit` as local commands that never call the LLM.
- [x] 3.3 Add `/status` output with active provider names and configured model names.
- [x] 3.4 Add `/history` rendering for recent retained user/assistant turns and `/clear` confirmation output.

## 4. Voice pipeline status UX improvements

- [x] 4.1 Standardize user-facing status labels (`[Ready]`, `[Recording]`, `[Recorded]`, `[Transcribing]`, `[Thinking]`, `[Speaking]`, `[Done]`).
- [x] 4.2 Show transcript and assistant response lines in a consistent, readable format for both voice and text paths.
- [x] 4.3 Ensure each completed request returns to a ready prompt with clear next-input guidance.
- [x] 4.4 Hide noisy internal logs unless `debug=true`.

## 5. Error handling and resilience

- [x] 5.1 Add user-friendly microphone failure handling with macOS privacy guidance.
- [x] 5.2 Add transcription failure handling that reports `[Error] Could not transcribe audio.` and safely returns to ready.
- [x] 5.3 Add Ollama connectivity error handling with `ollama serve` guidance.
- [x] 5.4 Add TTS failure handling that preserves text response, prints warning, and continues interaction loop.

## 6. Verification and regression checks

- [x] 6.1 Add or update tests for conversation manager behavior, especially max-turn trimming and clear/reset behavior.
- [x] 6.2 Add or update tests for command routing to ensure slash commands do not reach the LLM path.
- [x] 6.3 Add or update tests for LLM payload generation to confirm role-based message history is sent to Ollama.
- [x] 6.4 Run manual validation with `python app.py run` for voice flow, text follow-up flow, and command flow.
