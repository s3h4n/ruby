## 1. Interruption correctness hardening

- [x] 1.1 Rework barge-in monitor lifecycle so detection is active only during audible playback and guarded at chunk boundaries.
- [x] 1.2 Add interruption-state regression tests for inter-chunk silence to verify no false cancellation occurs.
- [x] 1.3 Verify intentional barge-in during active playback still cancels generation, synthesis, and playback quickly.

## 2. Caption/final output consistency

- [x] 2.1 Implement output ownership tracking for spoken chunks vs finalized assistant text.
- [x] 2.2 Suppress duplicated final response printing when live captions already covered the full response.
- [x] 2.3 Add residual-content fallback so only unseen trailing text is printed once when needed.

## 3. Acknowledgement variation quality

- [x] 3.1 Add acknowledgement phrase pool for long/tool-like requests in voice runtime behavior.
- [x] 3.2 Implement anti-repeat selection so adjacent qualifying turns do not reuse the same phrase.
- [x] 3.3 Add deterministic tests for acknowledgement diversity and no-regression direct-answer behavior.

## 4. Pipeline concurrency guarantees

- [x] 4.1 Add runtime invariants/instrumentation showing overlap of LLM streaming, TTS synthesis, and playback for multi-chunk responses.
- [x] 4.2 Add integration tests that fail if pipeline behavior regresses into effectively serial execution.
- [x] 4.3 Tune queue/chunk timing parameters for sustained overlap without starvation during long responses.

## 5. Production verification and polish

- [x] 5.1 Run targeted runtime suites for interruption, caption consistency, acknowledgement variation, and chunk continuity.
- [x] 5.2 Run full test suite and validate no regressions in CLI entrypoint contracts.
- [x] 5.3 Update OpenSpec tasks progress and document final tuning values/observability notes in relevant artifacts.
