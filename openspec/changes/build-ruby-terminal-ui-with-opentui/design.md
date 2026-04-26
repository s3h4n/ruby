## Context

Ruby is a Python-first local assistant with working runtime behavior (voice capture, transcription, model orchestration, tools, speech output) and canonical CLI entrypoints (`python app.py <command>` and `python -m ruby <command>`). The current operator experience is a runner-style CLI, which limits visibility into live states and makes pause/interrupt/tool activity harder to understand.

This change introduces an OpenTUI frontend as a separate presentation layer while preserving runtime ownership in Python. The design must protect existing command behavior, keep responsibilities clean across backend and frontend layers, and prepare for future non-terminal frontends using the same contract.

## Goals / Non-Goals

**Goals:**
- Add a production-quality terminal UI frontend implemented with Bun + TypeScript + OpenTUI.
- Define a stable command/event bridge so frontends communicate with backend runtime through structured messages only.
- Preserve existing runner behavior and add a new `tui` command without breaking current CLI contracts.
- Expose runtime states, streaming, tool lifecycle, pause/resume, interrupt, and recoverable errors in real time.
- Ensure TTS speaks Markdown-cleaned text while conversation display keeps original Markdown.
- Provide mock mode and test coverage for bridge/state/speech normalization behavior.

**Non-Goals:**
- Replacing assistant orchestration, model providers, tool execution, or speech engines.
- Building a web frontend in this change.
- Introducing auth, persistence, or cross-machine transport protocols.
- Reworking command semantics unrelated to TUI integration.

## Decisions

### 1) Keep Python runtime as single source of truth
The backend continues to own recording/transcription/model/tool/speech lifecycles. The TUI is read/write at the boundary only (receive events, send commands).

- Alternatives considered:
  - Move model/tool logic to TypeScript: rejected due to duplicated logic and higher regression risk.
  - Split runtime ownership by feature: rejected due to state drift between layers.

### 2) Use JSONL over stdio for bridge transport
The bridge uses line-delimited JSON messages between a spawned Python runtime process and the TypeScript TUI process. This minimizes dependencies and works well for local terminal execution.

- Alternatives considered:
  - WebSocket/HTTP local server: rejected as unnecessary process/network complexity for first frontend.
  - Named pipes/domain sockets: rejected for portability and setup overhead versus stdio.

### 3) Formalize shared contracts for commands/events
Command and event types are centralized in bridge contract modules (Python + TypeScript mirrors). Required state enums and payload fields are validated before dispatch.

- Alternatives considered:
  - Ad-hoc untyped payloads: rejected because errors become hard to diagnose and future frontends become brittle.
  - Frontend-specific contracts: rejected because contract reuse is a core architecture goal.

### 4) Add dedicated runtime mode for frontend streaming
Python runtime exposes a frontend-facing mode that emits structured events at key lifecycle points and accepts control commands (`input.text`, `voice.start/stop`, `assistant.pause/resume/interrupt`, `conversation.clear_visible`).

- Alternatives considered:
  - Instrument existing runner output parsing: rejected because parsing human-facing text logs is fragile.
  - Re-architect full runtime command loop first: rejected as too broad for this change.

### 5) Implement TUI as modular UI + state + bridge layers
`ruby/tui/` is structured by components, state stores, bridge adapters, and utility modules. UI never calls backend internals directly.

- Alternatives considered:
  - Single-file TUI app: rejected for maintainability and future frontend parity.
  - Embedding TypeScript in existing Python package root: rejected for unclear boundary ownership.

### 6) Add mock runtime adapter in frontend
A mock bridge simulates normal and failure/interrupt/pause sequences without requiring voice model dependencies. This enables deterministic UI development and CI-friendly tests.

- Alternatives considered:
  - Only integration testing against live runtime: rejected due to flakiness and developer friction.

### 7) Normalize speech text in Python before TTS dispatch
Introduce `markdown_to_speech_text(markdown: str) -> str` (or equivalent) in Python TTS pipeline. UI keeps original Markdown; spoken output uses cleaned text.

- Alternatives considered:
  - Clean Markdown in frontend: rejected because backend owns speech output and may serve non-TUI clients.
  - Disable Markdown in assistant output: rejected because readable rich formatting should remain in chat.

### 8) Make runtime status always explicit in UI
Every state shown in footer/status includes (a) current state label, (b) plain-English explanation, and (c) next valid actions. Interrupt preserves partial assistant output and emits explicit system note.

- Alternatives considered:
  - Silent state transitions: rejected because it causes user uncertainty and poor control UX.

## Risks / Trade-offs

- [Contract drift between Python and TypeScript] → Add centralized schema constants and parser tests for both sides.
- [Terminal keybinding conflicts across shells/OS terminals] → Prefer required bindings, provide safe alternatives, and document deviations.
- [Bridge deadlock or stalled stream handling] → Use non-blocking readers, heartbeat/error handling, and clear bridge-scope error events.
- [Markdown cleanup removes meaningful technical text] → Use conservative normalization with targeted rules and broad unit tests.
- [State over-noise in UI] → Distinguish user-facing state/system notes from debug-level internal logs.

## Migration Plan

1. Introduce bridge contract types and Python runtime event emission behind a frontend mode.
2. Implement `ruby/tui/` package with mock bridge first (`bun run tui:mock`).
3. Connect real bridge and wire CLI command (`python app.py tui`).
4. Add markdown-to-speech cleanup utility and tests in Python runtime.
5. Add frontend tests for event parsing/state transitions/commands/mock behavior.
6. Update docs, CLI help text, and architecture notes.
7. Validate that existing runner (`python app.py run`) remains behaviorally unchanged.

Rollback strategy:
- Keep TUI isolated behind its own command path; if unstable, disable/hide `tui` command while leaving `run` unchanged.
- Runtime event emission can be guarded by frontend mode so existing runner flow is unaffected.

## Open Questions

- Should the initial bridge protocol version be explicitly versioned in each event payload (e.g., `protocolVersion`), or deferred until second frontend appears?
- Should terminal resize events be bridged from frontend to backend now, or handled entirely in frontend layout state for v1?
