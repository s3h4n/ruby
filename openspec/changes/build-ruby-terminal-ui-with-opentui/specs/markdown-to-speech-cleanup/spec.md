## ADDED Requirements

### Requirement: Speech text normalization stage
The system SHALL normalize assistant Markdown output into speech-friendly plain text before passing content to TTS.

#### Scenario: Assistant response is spoken
- **WHEN** assistant text is sent to speech output
- **THEN** the runtime SHALL call a Markdown-to-speech normalization function
- **AND** TTS SHALL receive normalized text rather than raw Markdown

### Requirement: Visible and spoken text separation
The system SHALL preserve original assistant Markdown for conversation display while using normalized text only for speech output.

#### Scenario: Markdown formatting remains visible in UI
- **WHEN** an assistant message contains headings, emphasis, code blocks, or links
- **THEN** the conversation output SHALL keep original Markdown formatting
- **AND** spoken output SHALL omit Markdown control syntax

### Requirement: Markdown cleanup rules
Normalization SHALL preserve meaning while removing or transforming Markdown syntax that is unnatural when spoken.

#### Scenario: Formatting markers are removed
- **WHEN** text contains heading markers, emphasis markers, or code fence markers
- **THEN** speech text SHALL exclude raw marker tokens such as `#`, `**`, `_`, and triple backticks

#### Scenario: Inline code and links are transformed
- **WHEN** text contains inline code and Markdown links
- **THEN** inline code SHALL be spoken as its code content without backticks
- **AND** links SHALL prefer speaking the human-readable label instead of Markdown URL syntax

#### Scenario: Lists and tables are made speech-friendly
- **WHEN** text contains bullet lists, numbered lists, or Markdown tables
- **THEN** speech text SHALL convert them into readable sequence phrasing with natural pauses
- **AND** table pipes and separator rows SHALL not be spoken literally

### Requirement: Conservative normalization behavior
Normalization SHALL avoid over-stripping normal text and SHALL preserve semantic meaning of technical content.

#### Scenario: Plain text remains intact
- **WHEN** text contains no Markdown control syntax
- **THEN** normalization SHALL return equivalent plain text content without unnecessary alteration

### Requirement: Markdown-to-speech test coverage
The system SHALL include automated tests for normalization behavior across representative Markdown patterns.

#### Scenario: Required markdown cases are tested
- **WHEN** tests run for speech normalization
- **THEN** there SHALL be explicit coverage for headings, bold, italic, inline code, code blocks, links, bullet lists, numbered lists, tables, and mixed Markdown responses
