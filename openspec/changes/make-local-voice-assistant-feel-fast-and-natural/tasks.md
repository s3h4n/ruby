## 1. Streaming foundations

- [x] 1.1 Extend the Ollama provider/client to support streamed response output and first-token timing capture.
- [x] 1.2 Add runtime plumbing in the assistant orchestration path to consume streamed LLM output incrementally.
- [x] 1.3 Add/update unit tests for streamed provider behavior and non-stream fallback compatibility.

## 2. Speech chunking

- [x] 2.1 Implement a speech chunker that buffers partial LLM text and emits natural chunks by punctuation/phrase timeout.
- [x] 2.2 Add chunking configuration (`min_chunk_words`, `max_chunk_words`, `max_chunk_wait_ms`) and defaults/migration wiring.
- [x] 2.3 Add tests for chunk boundary behavior, short-answer handling, and markdown/code-fragment suppression.

## 3. Concurrent TTS and playback queues

- [x] 3.1 Implement a non-blocking TTS synthesis queue that accepts chunked text while generation continues.
- [x] 3.2 Implement a playback queue that can play synthesized audio while additional chunks are synthesized.
- [x] 3.3 Add queue lifecycle handling for normal completion, cancellation, and shutdown safety.

## 4. VAD turn capture and fallback modes

- [x] 4.1 Add `recording_mode` support for `vad`, `fixed`, and `manual`, with `vad` default.
- [x] 4.2 Implement VAD turn detection with pre-roll, silence-based turn end, minimum speech length, and max-turn limit.
- [x] 4.3 Preserve existing fixed-duration recording path as fallback/debug mode and verify behavior parity.

## 5. Interruption (barge-in) handling

- [x] 5.1 Add barge-in detection while assistant audio is speaking and route detection to a shared cancellation coordinator.
- [x] 5.2 Cancel active/pending generation, synthesis, and playback work for interrupted turns and clear stale queues.
- [x] 5.3 Ensure interrupted assistant output is not committed as a completed assistant message in conversation memory.

## 6. Voice behavior policy

- [x] 6.1 Add or update voice-mode system instructions for concise spoken responses and no fake tool claims.
- [x] 6.2 Implement acknowledgement heuristic for long/tool-like tasks and keep short/simple responses direct.
- [x] 6.3 Add tests for direct short-answer behavior and acknowledgement-first behavior on long tasks.

## 7. CLI states and latency observability

- [x] 7.1 Add stable CLI state feedback (`Listening`, `Transcribing`, `Thinking`, `Speaking`, `Interrupted`, `Done`).
- [x] 7.2 Add latency checkpoint instrumentation for end-of-speech->transcript, transcript->first-token, first-token->first-chunk, first-chunk->first-TTS-audio, first-TTS-audio->playback-start, and barge-in->audio-stop.
- [x] 7.3 Gate latency output behind debug/latency config and add tests for log emission behavior.

## 8. Config + integration + tuning

- [x] 8.1 Add new config fields to `ruby/config/settings.py` defaults and mirror them in `config.example.json`.
- [x] 8.2 Run CLI/runtime integration checks to validate streamed path, fallback recording modes, and interruption flow.
- [x] 8.3 Tune default timing/chunk thresholds for perceived responsiveness and update documentation/comments where needed.
