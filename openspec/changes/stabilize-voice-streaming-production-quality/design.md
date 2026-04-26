## Context

The current streamed voice runtime is close to the intended architecture but still fails production expectations under realistic conversational patterns. Reported behavior includes mid-turn interruption during long answers, repeated acknowledgement phrasing, and duplicated text output where chunk-level captions are followed by the same full response again. These issues reduce trust in correctness and make the UX feel unstable even when latency is good.

The implementation area is cross-cutting: barge-in detection in recorder/CLI coordination, chunk caption/final text rendering policy, acknowledgement strategy in assistant behavior, and queue overlap guarantees across LLM streaming, TTS synthesis, and playback. The solution must preserve local-only execution and existing entrypoint contracts.

## Goals / Non-Goals

**Goals:**
- Eliminate false interruption during assistant output while preserving intentional barge-in responsiveness.
- Guarantee text output consistency: live chunk captions and final text display must never duplicate content.
- Replace repetitive acknowledgement phrases with varied, policy-controlled acknowledgements for long/tool-like tasks.
- Enforce and verify concurrent overlap of generation, synthesis, and playback for long responses.
- Add testable production guardrails for quality, completion integrity, and throughput.

**Non-Goals:**
- Replacing Whisper/Ollama/Kokoro provider stack.
- Introducing remote orchestration or cloud dependencies.
- Redesigning the CLI interaction model beyond runtime correctness and quality hardening.

## Decisions

### 1) Treat interruption as playback-scoped with explicit guard windows
- **Decision:** Keep barge-in detection active only while audio is actively playing and add a short guard window around chunk boundaries to avoid race-triggered cancellation from silence transitions.
- **Rationale:** Most false interrupts occur in inter-chunk silence and edge timing windows, not during actual speech playback.
- **Alternatives considered:**
  - Always-on detector during the entire turn lifecycle. Rejected: continues to trigger on silent gaps.
  - Disable barge-in for long tasks. Rejected: degrades expected interactive behavior.

### 2) Canonical output ownership between captions and final response
- **Decision:** Introduce a single rendering policy: if chunk captions were emitted, final text print is suppressed unless there is unseen residual text not covered by spoken chunks.
- **Rationale:** Prevents duplicate visible output while preserving complete content in edge cases.
- **Alternatives considered:**
  - Always print both chunk captions and final text. Rejected: duplicates content.
  - Print final text only, remove captions. Rejected: hurts perceived responsiveness.

### 3) Acknowledgement variation with deterministic anti-repeat rules
- **Decision:** Add an acknowledgement phrase pool and avoid reusing the same phrase in adjacent turns; rotate by history-aware selection.
- **Rationale:** Repetition makes runtime sound robotic and lowers perceived quality.
- **Alternatives considered:**
  - Keep a single fixed phrase. Rejected: repetitive UX.
  - Fully random phrase generation by LLM. Rejected: inconsistent and hard to test.

### 4) Concurrency contracts for pipeline overlap
- **Decision:** Define runtime overlap invariants and expose debug checkpoints proving that LLM stream consumption, TTS synthesis, and playback can all be in-flight concurrently for multi-chunk answers.
- **Rationale:** Existing queue architecture supports overlap but lacks explicit contract checks and regression tests for sustained concurrency.
- **Alternatives considered:**
  - Best-effort overlap without assertions. Rejected: regressions can silently reintroduce serial behavior.

### 5) Production-quality regression suite for failure signatures
- **Decision:** Add focused runtime tests for false interruption, duplicate output suppression, acknowledgement variety, and long-response continuity under pauses.
- **Rationale:** User-reported failures are behavioral and must be guarded by scenario-based runtime tests.
- **Alternatives considered:**
  - Rely only on manual runtime testing. Rejected: too brittle for production confidence.

## Risks / Trade-offs

- **[Risk]** Tight interruption gating could delay legitimate barge-in by a small margin. -> **Mitigation:** Keep guard windows short and benchmark barge-in-to-audio-stop latency.
- **[Risk]** Caption/final-text reconciliation logic may miss rare residual fragments. -> **Mitigation:** Track emitted text boundaries and add residual-only fallback print tests.
- **[Risk]** Acknowledgement rotation may sound deterministic over long sessions. -> **Mitigation:** Use a small phrase pool with deterministic anti-adjacent-repeat rotation.
- **[Risk]** Additional synchronization checks may increase complexity. -> **Mitigation:** Isolate overlap instrumentation and keep it behind debug/latency flags.

## Migration Plan

1. Implement interruption guard-window and playback-scoped detection refinements.
2. Add caption/final-text ownership policy and deduplication logic.
3. Introduce acknowledgement variation pool and turn-to-turn anti-repeat behavior.
4. Add pipeline overlap assertions/metrics and scenario tests.
5. Run full runtime/test verification and tune thresholds for perceived speed + stability.

Rollback strategy:
- Revert to current stable playback-scoped interruption without guard-window optimization.
- Disable acknowledgement variation via configuration fallback to existing behavior.
- Keep overlap instrumentation optional so runtime behavior can remain unchanged if metrics are disabled.

## Final tuning + observability notes

- Barge-in guard window is tuned to 20 ms around chunk boundaries to suppress immediate false spikes while preserving intentional interruption during active playback.
- Chunking now emits one sentence at a time and protects common abbreviation/acronym/decimal periods from being treated as sentence endings.
- Final-output rendering uses caption ownership with residual-only print fallback to avoid full-response duplication after live captions.
- Debug telemetry now includes `playback_start_to_stream_complete` and an overlap boolean debug line (`playback_started_before_stream_complete=true|false`) to make concurrency regressions visible.
- Voice policy tightened for speech-first output: single paragraph, short responses, and no table/bullet/markdown-heavy formatting.

## Open Questions

- Should acknowledgement variation be globally seeded per session or randomized per turn with anti-repeat only?
- What minimum overlap threshold should be treated as regression in tests (event ordering only vs timing bounds)?
- Should deduplication use text normalization (whitespace/punctuation-insensitive) or strict string matching?
