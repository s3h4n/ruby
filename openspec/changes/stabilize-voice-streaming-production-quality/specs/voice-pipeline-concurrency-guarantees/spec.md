## ADDED Requirements

### Requirement: Voice pipeline stages SHALL overlap during multi-chunk responses
For responses that produce multiple chunks, LLM streaming, TTS synthesis, and playback SHALL run concurrently rather than strictly serially.

#### Scenario: Generation continues while previous chunk is synthesized and played
- **WHEN** chunk N is being played and chunk N+1 is being synthesized
- **THEN** LLM streaming may continue producing additional text for subsequent chunks

### Requirement: Queue flow SHALL prevent downstream starvation after first chunk
After first playback starts, the pipeline SHALL continue feeding synthesis and playback queues until completion unless interruption is triggered.

#### Scenario: Long response proceeds without mid-pipeline stall
- **WHEN** the first chunk has started playback and no interruption signal is raised
- **THEN** subsequent chunks are synthesized and played without requiring full-response completion first

### Requirement: Concurrency behavior SHALL be observable in debug telemetry
When latency debug mode is enabled, runtime logs SHALL expose checkpoint ordering that demonstrates overlapping pipeline work.

#### Scenario: Debug output includes overlap-relevant checkpoints
- **WHEN** a multi-chunk response runs in debug latency mode
- **THEN** the runtime emits checkpoint logs that show first-token, first-chunk, first-audio, and playback-start progression without full-response wait
