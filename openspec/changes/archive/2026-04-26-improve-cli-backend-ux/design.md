## Context

Ruby currently operates as a terminal-first local assistant pipeline (record audio -> transcribe -> generate response -> speak response). The present interaction hides most intermediate states, does not preserve in-session context, and only reliably supports single-turn prompts. This creates low user trust and makes backend integration hard to validate before any frontend exists.

The requested scope is backend/CLI only: preserve current providers (whisper.cpp, Ollama, Kokoro), keep model selection behavior unchanged, and avoid introducing web/frontend frameworks.

## Goals / Non-Goals

**Goals:**
- Provide deterministic and readable CLI state progression for voice and text requests.
- Support mixed input at a single prompt: Enter for recording, typed text for chat, slash commands for control.
- Add bounded in-memory conversation history and pass it to Ollama as a full role-based message array.
- Ensure user-facing failures are recoverable and return to a usable ready state.
- Add debug gating so operator-focused logs are available without polluting normal UX.

**Non-Goals:**
- No frontend/UI framework work.
- No persistent memory storage across sessions.
- No provider/model replacement or model routing changes.
- No streaming output redesign for Ollama responses in this change.

## Decisions

### Decision: Introduce a dedicated ConversationManager
Create `ruby/core/conversation.py` to own history lifecycle: append user/assistant turns, trim to `max_turns`, expose `get_messages(system_prompt)` for LLM calls, and clear/reset state.

**Rationale:** centralizes state policy and keeps CLI, provider, and orchestration layers decoupled.

**Alternatives considered:**
- Keep history as ad-hoc lists in the CLI loop: rejected due to coupling and harder testing.
- Persist to disk now: rejected because persistence is explicitly out of scope.

### Decision: Standardize CLI state labels and transition order
Use a fixed set of user-visible labels (`[Ready]`, `[Recording]`, `[Recorded]`, `[Transcribing]`, `[Thinking]`, `[Speaking]`, `[Done]`) and optional content markers such as transcript and final response lines.

**Rationale:** predictable state transitions improve user trust and make manual QA easier.

**Alternatives considered:**
- Keep current sparse logging: rejected due to unclear progress.
- Add rich terminal UI library: rejected to keep dependencies minimal.

### Decision: Single prompt supports text, voice, and command control
At `Ruby >` prompt:
- empty input => start voice recording path
- non-empty non-command => text message path
- slash commands => local command handlers (`/help`, `/history`, `/clear`, `/status`, `/quit`)

**Rationale:** improves test speed and discoverability without mode switching.

**Alternatives considered:**
- Separate text/voice modes: rejected as more cognitive overhead.
- Voice-only flow: rejected because rapid iteration requires text path.

### Decision: LLM adapter always receives normalized message arrays
Refactor LLM provider contract to accept `messages: list[dict[str, str]]` and send that list directly to Ollama `/api/chat` with `stream=false`.

**Rationale:** enables context-aware follow-ups and aligns provider interface with modern chat APIs.

**Alternatives considered:**
- Keep single-prompt calls: rejected because follow-up intent is lost.
- Encode history into one concatenated prompt string: rejected due to weaker role separation.

### Decision: User-safe error surface with debug expansion
Map common failures to concise user-facing messages; expose raw exceptions, subprocess details, and path/provider internals only when `debug=true`.

**Rationale:** balances clean UX with operational diagnosability.

**Alternatives considered:**
- Always verbose errors: rejected due to noisy UX.
- Silent retries only: rejected because users need actionable feedback.

## Risks / Trade-offs

- **[History truncation may drop relevant context]** -> Mitigation: keep configurable `max_turns` and include `/history` for quick verification.
- **[Status output can drift from actual state transitions]** -> Mitigation: centralize transitions in one pipeline orchestration path and test each branch.
- **[Provider contract refactor may break existing call sites]** -> Mitigation: update all LLM invocation points in one change and add adapter-level tests for payload shape.
- **[TTS/STT recoverable failures could still break loop continuity]** -> Mitigation: enforce exception boundaries around each stage and always return to ready prompt.

## Migration Plan

1. Add configuration fields (`conversation.enabled`, `conversation.max_turns`, `debug`) with defaults preserving existing runtime behavior when possible.
2. Introduce ConversationManager and wire CLI loop to maintain per-session state.
3. Refactor LLM provider entrypoints to accept message arrays and update Ollama request body.
4. Implement slash command handlers and mixed input routing at the primary prompt.
5. Add/adjust tests for command parsing, history trimming, message payload generation, and error handling branches.
6. Validate manually with `python app.py run` across voice flow, text follow-up flow, and command flow.
7. Rollback approach: disable conversation in config and revert to previous single-turn behavior if severe regressions appear.

## Open Questions

- Should `[Transcript ready]` and `[Response ready]` be printed as explicit labels in addition to `You said:` and `Ruby:` lines, or should those lines be the readiness markers?
- Should `/history` display all retained turns or a capped display window (e.g., last 5) while retaining full in-memory max turns?
- Should `/status` include resolved binary/provider executable paths in debug mode only or always show basic provider names and models?
