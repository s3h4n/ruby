## Why

The current voice loop is strictly sequential (record -> full STT -> full LLM -> full TTS -> playback), which makes the assistant feel slow and non-conversational even when each component works correctly. We need to optimize for perceived responsiveness by streaming generation and speech, while preserving the existing local-only architecture.

## What Changes

- Replace the linear voice loop with a streamed, interruptible pipeline: turn detection -> STT -> streamed LLM -> speech chunking -> queued TTS -> queued playback.
- Add VAD-based turn ending with pre-roll buffering and configurable silence thresholds, while keeping fixed-duration/manual recording as supported fallback modes.
- Add Ollama streaming support to produce text incrementally and start speech from the first useful phrase instead of waiting for full completion.
- Add a speech chunker that emits natural sentence/phrase units and skips markdown/code-heavy fragments.
- Add asynchronous Kokoro synthesis and non-blocking playback queues so upcoming chunks can be synthesized while current audio is playing.
- Add barge-in interruption so user speech can cancel pending generation/synthesis/playback quickly.
- Add voice-specific response behavior: concise spoken style plus short acknowledgements for long/tool-like tasks when appropriate.
- Add clear CLI runtime states and optional latency logs for key pipeline timings.
- Enforce clean conversation memory for streamed/interrupted responses (store only final user transcript and completed assistant replies).

## Capabilities

### New Capabilities
- `streamed-voice-turn-pipeline`: End-to-end streamed voice response pipeline from turn completion to first audio playback.
- `adaptive-voice-turn-capture`: Configurable VAD-based speech turn capture with fallback recording modes.
- `interruptible-voice-playback`: Barge-in aware cancellation and concurrent TTS/playback queue coordination.
- `voice-response-behavior-and-observability`: Spoken-style response behavior, CLI state feedback, and latency instrumentation.

### Modified Capabilities
- None.

## Impact

- Affected runtime orchestration in `ruby/app.py`, `ruby/core/assistant.py`, and CLI flow in `ruby/interfaces/cli.py`.
- Likely changes in provider interfaces and implementations for Ollama streaming, STT turn-capture flow, and Kokoro TTS scheduling.
- Configuration schema updates in `ruby/config/settings.py` and `config.example.json` for voice streaming/VAD/chunking/interruption/latency options.
- New or updated tests for CLI runtime behavior, streaming pipeline ordering, interruption handling, and config defaults/migration.
