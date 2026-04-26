## 1. Backend bridge contracts

- [ ] 1.1 Define shared runtime state/event/command schemas for frontend mode (Python contract module + mirrored TypeScript types).
- [ ] 1.2 Add frontend runtime bridge mode that reads JSONL commands from stdin and emits JSONL events to stdout.
- [ ] 1.3 Emit `state.changed`, conversation, tool lifecycle, and recoverable `error` events at existing runtime lifecycle boundaries.
- [ ] 1.4 Add backend-side validation and graceful error handling for unknown or malformed frontend commands.

## 2. OpenTUI project scaffold and app shell

- [ ] 2.1 Create `ruby/tui/` Bun + TypeScript OpenTUI project structure with scripts for `tui` and `tui:mock`.
- [ ] 2.2 Implement baseline TUI layout components (header, conversation view, tool activity region, input/footer, shortcut help).
- [ ] 2.3 Implement centralized frontend state stores for runtime state, conversation stream, active tools, and transient system notices.

## 3. Mock runtime and UI behavior

- [ ] 3.1 Implement mock bridge adapter that simulates normal lifecycle (idle -> recording -> transcribing -> user message -> thinking -> streaming -> speaking -> idle).
- [ ] 3.2 Add mock scenarios for interrupt during thinking/streaming, pause during speaking, backend error, and terminal resize.
- [ ] 3.3 Wire mock mode script (`bun run tui:mock`) to run the TUI without backend voice/model dependencies.

## 4. Real bridge integration and controls

- [ ] 4.1 Implement Python process bridge in TUI (`python app.py tui` path) and map bridge events into frontend state updates.
- [ ] 4.2 Implement command dispatch from keyboard/input interactions (`input.text`, voice start/stop, pause/resume, interrupt, clear visible conversation).
- [ ] 4.3 Ensure interrupt flow preserves partial assistant output, shows interruption note, and returns to idle.
- [ ] 4.4 Ensure pause flow updates UI state immediately and supports clean resume/interrupt actions.
- [ ] 4.5 Implement keyboard shortcut bindings and document safe alternative mappings for any terminal conflicts.

## 5. Markdown-to-speech cleanup

- [ ] 5.1 Add `markdown_to_speech_text` (or equivalent) in Python speech path to normalize Markdown before TTS dispatch.
- [ ] 5.2 Implement cleanup rules for headings, emphasis, code fences/inline code, links, bullet/numbered lists, and tables while preserving meaning.
- [ ] 5.3 Ensure visible conversation content remains original Markdown while speech uses normalized text only.
- [ ] 5.4 Add unit tests covering headings, bold, italic, inline code, code blocks, links, bullet lists, numbered lists, tables, and mixed Markdown.

## 6. CLI integration, tests, and docs

- [ ] 6.1 Add CLI command routing/help text for `python app.py tui` while preserving `python app.py run` behavior.
- [ ] 6.2 Add/extend tests for bridge event parsing, command handling, state transitions, pause/interrupt behavior, mock mode flows, and resize handling where feasible.
- [ ] 6.3 Update `README.md` and relevant project docs with architecture layering, run instructions (`app.py tui`, `bun run tui`, `bun run tui:mock`), voice states, pause/interrupt behavior, and speech cleanup behavior.
- [ ] 6.4 Run project verification commands and confirm no regressions in existing CLI entrypoint behavior.
