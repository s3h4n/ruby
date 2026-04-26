## Context

The current CLI voice runtime uses a blocking sequence: capture audio, run full transcription, request full LLM completion, synthesize full TTS, then start playback. This architecture is correct but produces high perceived latency and does not support interruption during assistant speech. The change must remain fully local and compatible with existing runtime contracts (`python app.py <command>` and `python -m ruby <command>`), Whisper-based STT, Ollama/Gemma 4 inference, and Kokoro TTS.

The implementation spans multiple modules: runtime orchestration, provider streaming APIs, audio input/output behavior, config schema, and CLI state telemetry. Existing fallback behaviors must remain available for debugging and constrained environments.

## Goals / Non-Goals

**Goals:**
- Deliver streamed voice responses where playback can start from the first useful phrase, not full completion.
- Add configurable VAD-based turn-ending while preserving `fixed` and `manual` recording modes.
- Enable concurrent generation/synthesis/playback through chunking and producer-consumer queues.
- Support barge-in interruption that cancels pending response work and stops playback quickly.
- Improve CLI observability with explicit state transitions and optional latency timings.
- Keep conversation memory clean by storing only final user transcripts and completed assistant messages.

**Non-Goals:**
- Building a GUI or web frontend.
- Replacing core providers (Whisper, Ollama, Kokoro) with different stacks.
- Implementing speculative multi-model decoding or distributed infrastructure.
- Rewriting the entire assistant architecture when incremental extension is sufficient.

## Decisions

### 1) Introduce a streamed orchestration pipeline in the assistant runtime
- **Decision:** Add a staged runtime pipeline with explicit boundaries: turn capture -> transcript -> streamed LLM tokens -> speakable chunk emission -> TTS queue -> playback queue.
- **Rationale:** Keeps compatibility with current module layout while allowing overlapping work and latency instrumentation at each stage.
- **Alternatives considered:**
  - Fully rewrite runtime as a new framework-specific event loop. Rejected: high migration risk and unnecessary scope.
  - Keep linear flow and only optimize model speed. Rejected: does not improve perceived latency enough.

### 2) Use Ollama streaming as a first-class provider interface
- **Decision:** Extend the Ollama provider/client to expose streamed text chunks/tokens and first-token timing.
- **Rationale:** Streaming is mandatory to begin TTS before completion and to keep generation active during playback.
- **Alternatives considered:**
  - Polling complete responses. Rejected: preserves blocking behavior.

### 3) Add a dedicated speech chunker for natural speech units
- **Decision:** Buffer streamed text and emit chunks on sentence punctuation, long-clause commas, or max-wait timeout, constrained by min/max word bounds.
- **Rationale:** Produces natural spoken cadence and prevents one-token TTS thrash.
- **Alternatives considered:**
  - Emit per-token/per-word chunks. Rejected: robotic and inefficient.
  - Wait for full paragraphs. Rejected: too much delay.

### 4) Use asynchronous producer-consumer queues for TTS and playback
- **Decision:** Introduce non-blocking queues between chunk generation, Kokoro synthesis, and audio playback.
- **Rationale:** Enables concurrent chunk N playback while chunk N+1 synthesis proceeds, reducing dead air.
- **Alternatives considered:**
  - Single-threaded blocking synthesis+playback loop. Rejected: no overlap, high latency.

### 5) Add VAD with configuration-gated fallback modes
- **Decision:** Support `recording_mode` values `vad`, `fixed`, and `manual`; default to `vad`. In `vad`, end turn by silence timeout with pre-roll and minimum speech duration constraints.
- **Rationale:** Better natural turn detection while preserving debuggability and backwards-safe fallbacks.
- **Alternatives considered:**
  - Remove fixed/manual capture modes. Rejected: harms reliability and diagnostics.

### 6) Treat barge-in as a cancellation signal across active stages
- **Decision:** On detected interruption, atomically signal cancellation for pending LLM stream consumption, queued-but-unplayed audio, and active playback.
- **Rationale:** Fast interruption requires coordinated cancellation, not playback-only stop.
- **Alternatives considered:**
  - Stop only current audio output. Rejected: stale queued chunks would continue later.

### 7) Add voice response style policy and acknowledgement heuristic
- **Decision:** Use a voice-mode system instruction focused on concise spoken output, plus runtime heuristic to prepend short acknowledgement for long/tool-like tasks only.
- **Rationale:** Improves perceived responsiveness without adding filler to short questions.
- **Alternatives considered:**
  - Always acknowledge every request. Rejected: repetitive and unnatural.
  - Prompt-only behavior without runtime heuristic. Rejected: less controllable and testable.

### 8) Add structured latency checkpoints and CLI states
- **Decision:** Emit stable CLI states (`Listening`, `Transcribing`, `Thinking`, `Speaking`, `Interrupted`, `Done`) and optional debug timing metrics for stage boundaries.
- **Rationale:** Enables iterative tuning and confidence in perceived-speed improvements.
- **Alternatives considered:**
  - Ad-hoc debug logs only. Rejected: harder to interpret and test.

## Risks / Trade-offs

- **[Risk]** Queue coordination introduces race conditions around interruption and shutdown. -> **Mitigation:** Centralize cancellation token/state and enforce queue drain semantics in one coordinator.
- **[Risk]** VAD thresholds may cut words or delay turn end across different microphones/environments. -> **Mitigation:** Provide configurable defaults and retain `fixed`/`manual` fallback modes.
- **[Risk]** Chunking can emit awkward segments for punctuation-poor responses. -> **Mitigation:** Add max-wait flush and min/max word guardrails.
- **[Risk]** Streaming plus background synthesis can raise CPU usage on local machines. -> **Mitigation:** Bound queue size and tune chunk sizes; expose config for conservative settings.
- **[Risk]** Conversation memory may capture interrupted replies if not carefully finalized. -> **Mitigation:** Commit assistant messages only on successful completion and mark interrupted responses internally.

## Migration Plan

1. Add streaming and chunking interfaces behind config flags while keeping existing linear behavior available.
2. Introduce queue-based TTS/playback path and validate no regression in non-streamed fallback mode.
3. Add VAD mode and preserve fixed/manual capture; set default to `vad` only after compatibility checks.
4. Add interruption handling and latency logs; confirm contracts with CLI behavior tests.
5. Roll out tuned defaults in `config.example.json` and config migration logic, keeping strict config validation rules.

Rollback strategy:
- Switch `voice.mode` and/or `recording_mode` back to legacy-compatible values (`fixed`/non-streamed path) through config.
- Keep old path callable until new pipeline is validated by tests and runtime smoke checks.

## Open Questions

- Which existing audio input utility is the most stable insertion point for VAD pre-roll buffering?
- Should acknowledgement text be synthesized as its own high-priority chunk or integrated into first LLM chunk for easier interruption semantics?
- Are there existing provider abstractions for cancellation signals, or should a new shared cancellation context be introduced?
