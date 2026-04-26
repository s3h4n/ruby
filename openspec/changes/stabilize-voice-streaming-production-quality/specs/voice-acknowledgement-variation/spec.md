## ADDED Requirements

### Requirement: Long-running voice tasks SHALL use varied acknowledgement phrases
For long or tool-like requests, the assistant SHALL select acknowledgements from a managed phrase set instead of a single fixed sentence.

#### Scenario: Long request uses acknowledgement phrase from pool
- **WHEN** a voice request is classified as long-running or tool-like
- **THEN** the runtime emits one acknowledgement phrase selected from the configured acknowledgement set

### Requirement: Adjacent turns SHALL avoid acknowledgement repetition
The assistant SHALL avoid using the same acknowledgement phrase in consecutive qualifying turns within a session.

#### Scenario: Two consecutive long requests get different acknowledgements
- **WHEN** two back-to-back qualifying long requests are handled in one session
- **THEN** the second acknowledgement phrase differs from the first
