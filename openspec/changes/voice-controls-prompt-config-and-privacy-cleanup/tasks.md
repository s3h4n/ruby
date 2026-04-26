## 1. Prompt Resource Externalization

- [x] 1.1 Create `prompts/system_prompt.md` and move the current assistant system prompt text out of `pipeline.py`.
- [x] 1.2 Add a prompt-loading helper used by `pipeline.py` to read `prompts/system_prompt.md`.
- [x] 1.3 Add clear developer-facing handling for missing/unreadable prompt file while keeping user-facing CLI output clean.
- [x] 1.4 Verify `pipeline.py` still owns message/input formatting and does not hardcode assistant identity text.

## 2. Recording Toggle and Interruption UX

- [x] 2.1 Update CLI input handling so Enter starts recording from `[Ready]`.
- [x] 2.2 Update recording input handling so Enter during `[Recording]` stops recording immediately and sends it.
- [x] 2.3 Preserve existing timeout-based stop as fallback when manual stop is not used.
- [x] 2.4 Add interruption handling for `Esc` and `Ctrl+C` that emits `[Interrupted]` and returns to `[Ready]`.

## 3. Shared Cancellation Across Pipeline Stages

- [x] 3.1 Introduce a shared cancellation primitive for the active voice session lifecycle.
- [x] 3.2 Wire cancellation checks into recording loop behavior and discard partial audio when canceled before finalization.
- [x] 3.3 Wire cancellation checks into transcription so canceled transcriptions do not transition to thinking.
- [x] 3.4 Wire cancellation checks into model generation and ignore late responses when cancellation occurs.
- [x] 3.5 Wire cancellation checks into TTS playback so speaking stops immediately on interrupt.

## 4. Privacy, Config, and Repository Hygiene

- [x] 4.1 Audit Whisper/audio/temp/transcript path usage and remove hardcoded absolute local paths.
- [x] 4.2 Add or update environment/config path resolution for machine-specific values (including `WHISPER_MODEL_PATH` if required).
- [x] 4.3 Add `.env.example` with safe placeholders and ensure `.env` remains ignored.
- [x] 4.4 Update `.gitignore` with project-safe entries for local recordings, transcripts, temp artifacts, caches, Python cache files, and OS noise.
- [x] 4.5 Sanitize user-facing errors/log output to prevent leaking local machine paths or raw stack traces in normal runtime flows.

## 5. Verification

- [x] 5.1 Run targeted runtime checks to confirm flow: `[Ready] -> [Recording] -> [Recorded] -> [Transcribing] -> [Thinking] -> [Speaking] -> [Done] -> [Ready]`.
- [x] 5.2 Verify interruption from recording, transcribing, thinking, and speaking always yields clean `[Interrupted]` then `[Ready]`.
- [x] 5.3 Run `python -m pytest -q` and resolve regressions related to CLI flow, config handling, and runtime errors.
