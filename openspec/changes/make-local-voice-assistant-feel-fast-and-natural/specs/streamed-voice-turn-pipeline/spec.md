## ADDED Requirements

### Requirement: Streamed LLM output SHALL drive incremental speech generation
The assistant runtime SHALL consume Ollama responses as a stream and SHALL process partial output without waiting for full completion.

#### Scenario: First chunk emitted before full response completion
- **WHEN** a user turn is transcribed and the LLM begins streaming output
- **THEN** the runtime emits at least one speakable chunk before the full LLM response is complete

### Requirement: Speakable chunks SHALL start playback early
The assistant SHALL start TTS synthesis and playback from the first useful phrase or sentence produced by the chunker instead of waiting for the final answer text.

#### Scenario: Playback starts from first useful chunk
- **WHEN** the chunker emits the first speakable chunk
- **THEN** the system begins TTS and starts playback as soon as the first audio chunk is ready

### Requirement: Pipeline stages SHALL run concurrently
The system SHALL allow LLM generation, chunking, TTS synthesis, and playback to overlap through queue-based coordination.

#### Scenario: Next chunk is synthesized during current playback
- **WHEN** chunk N is playing
- **THEN** chunk N+1 can be synthesized while playback of chunk N is still active

### Requirement: Completed responses SHALL be persisted once
Conversation memory SHALL store the final user transcript and one completed assistant response for successful turns.

#### Scenario: Successful streamed response is committed once
- **WHEN** a streamed response finishes without interruption
- **THEN** the assistant stores one finalized assistant message and does not store intermediate chunk text as separate messages
