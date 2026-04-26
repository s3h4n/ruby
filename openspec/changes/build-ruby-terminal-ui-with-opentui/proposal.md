## Why

Ruby already has a capable Python runtime, but it still feels like a developer-oriented runner instead of a polished local AI app. A dedicated OpenTUI frontend is needed now to make runtime state, conversation flow, and voice interactions visible and controllable in real time without changing core backend behavior.

## What Changes

- Add a Bun + TypeScript OpenTUI frontend that acts as a first-class terminal UI for Ruby.
- Introduce a structured frontend/backend bridge so the Python runtime emits typed events and accepts typed commands over a simple IPC channel.
- Expose runtime states, conversation streaming, tool activity, pause/resume, interrupts, and recoverable errors in the terminal UI.
- Add TUI launch support from the canonical Python CLI (`python app.py tui`) while preserving the existing runner (`python app.py run`) as fallback.
- Add mock mode for TUI development and demos without live voice/model dependencies.
- Add a Markdown-to-speech cleanup layer so TTS reads natural text instead of Markdown syntax.
- Update tests and documentation to reflect layered architecture (backend runtime + multiple frontends).

## Capabilities

### New Capabilities
- `runtime-event-bridge`: Structured event/command contract between Python runtime and frontends, including state, conversation, tool, and error events.
- `terminal-ui-opentui`: OpenTUI-based terminal frontend with real-time state rendering, conversation streaming, tool activity, keyboard shortcuts, and mock mode.
- `markdown-to-speech-cleanup`: Speech-safe Markdown normalization for TTS output while preserving original Markdown in visible conversation.

### Modified Capabilities
- None.

## Impact

- Affected code: CLI command routing, runtime event emission points, TTS text preparation path, new `ruby/tui/` frontend package, and shared contract modules.
- Affected interfaces: `python app.py` command list/help, new `tui` command, and IPC message schema between Python and TypeScript.
- Dependencies: Bun + OpenTUI + TypeScript for frontend; minimal Python-side serialization/bridge utilities.
- Systems impacted: local runtime UX, voice/interrupt/pause flows, docs, and developer workflow for frontend iteration.
