## ADDED Requirements

### Requirement: Live captions and final response text SHALL not duplicate each other
If chunk-level captions are printed while speaking, the runtime SHALL NOT print the same content again as a full final response line.

#### Scenario: Chunk captions already covered full response
- **WHEN** all spoken response content has already been displayed as live captions
- **THEN** the final assistant print step does not output duplicated full-text content

### Requirement: Final text output SHALL include any residual content not covered by captions
If live caption output does not include all finalized assistant text, the runtime SHALL print only the unseen residual content.

#### Scenario: Residual text appended after streamed chunk display
- **WHEN** final assistant text includes content that was not emitted in live captions
- **THEN** the runtime prints exactly the unseen residual content once
