## Why

Voice runtime still behaves inconsistently under real usage: responses can interrupt mid-answer, acknowledgements are repetitive, and text output duplicates after chunk playback. This change raises runtime behavior to production-level reliability and speed by hardening interruption handling, chunk display semantics, and end-to-end concurrency guarantees.

## What Changes

- Tighten interruption detection so assistant turns are only interrupted by genuine user barge-in, not silence gaps or playback timing races.
- Eliminate duplicate assistant text display by separating live chunk captions from final-response rendering rules.
- Add acknowledgement variation policy so long/tool-like requests use natural, non-repetitive starter phrases.
- Enforce true overlapped pipeline execution where LLM generation, TTS synthesis, and playback run concurrently during long responses.
- Add production-quality guardrails and observability for throughput, interruption correctness, and response completion integrity.

## Capabilities

### New Capabilities
- `voice-interruption-correctness`: Prevent false interruption while preserving fast, intentional barge-in behavior.
- `voice-caption-and-final-text-consistency`: Ensure live chunk captions and final assistant text do not duplicate or conflict.
- `voice-acknowledgement-variation`: Provide diverse acknowledgement phrases for long/tool-like tasks with anti-repetition rules.
- `voice-pipeline-concurrency-guarantees`: Guarantee concurrent LLM->chunking->TTS->playback overlap and define measurable throughput expectations.

### Modified Capabilities
- None.

## Impact

- Affected runtime orchestration in `ruby/interfaces/cli.py` and queue/chunk flow in `ruby/core/voice_pipeline.py`.
- May require assistant response policy updates in `ruby/core/assistant.py` and voice prompt files under `prompts/`.
- Adds/updates integration and regression tests in `tests/test_voice_runtime_streaming.py` and related pipeline tests.
- May introduce additional debug metrics/config checks in `ruby/config/settings.py` and `config.example.json` for production tuning.
