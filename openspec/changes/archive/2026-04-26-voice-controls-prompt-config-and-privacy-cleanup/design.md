## Context

Ruby currently has a working voice loop and stable state progression, but maintainability and control issues remain concentrated in runtime orchestration. Assistant identity text is embedded in `pipeline.py`, control input is mostly one-way (start + timeout), and interruption behavior is inconsistent across long-running stages. A separate privacy concern exists where Whisper-related local machine paths can appear in config/error surfaces. This change must preserve the existing working flow and tool behavior while adding safer control and privacy guarantees.

## Goals / Non-Goals

**Goals:**
- Externalize assistant system prompt content into a reusable prompt resource and load it at runtime.
- Preserve current message formatting behavior while removing hardcoded assistant identity text from `pipeline.py`.
- Add Enter toggle control for recording start/stop, while keeping timeout auto-stop fallback.
- Add interruption (`Esc`/`Ctrl+C`) that cancels active stage work and returns to `[Ready]` cleanly.
- Introduce shared cancellation signaling so canceled stage results cannot continue downstream.
- Remove hardcoded/local path leakage from Whisper and related runtime output, and establish safe env/config patterns.
- Keep normal CLI UX clean (no raw tracebacks/private paths during normal interruption and expected runtime errors).

**Non-Goals:**
- No redesign of the app architecture or state model.
- No tool-calling behavior changes.
- No memory feature work.
- No multi-model routing implementation in this iteration.
- No personality/content changes beyond moving existing prompt text out of Python source.

## Decisions

### 1) Prompt resource externalization
`pipeline.py` will load a prompt file from `prompts/system_prompt.md` using a dedicated prompt-loading helper. The helper will provide a clear developer-facing exception if the file is missing/unreadable.

**Rationale:** Separates assistant identity from runtime orchestration and allows later reuse by multiple providers.

**Alternatives considered:**
- Keep prompt inline in Python constants: rejected (hard to maintain/reuse).
- Store prompt in config JSON: rejected (mixes large authored content with machine config).

### 2) Enter as recording toggle with timeout fallback
Input handling will treat Enter as a state-dependent action:
- `[Ready]` + Enter: start recording
- `[Recording]` + Enter: stop and finalize recording immediately

Timeout auto-stop remains unchanged as a fallback if manual stop is not used.

**Rationale:** Improves operator control without removing current reliability behavior.

**Alternatives considered:**
- Replace timeout with manual-only stop: rejected (regresses unattended behavior).

### 3) Shared cancellation event across long-running stages
Introduce one session-scoped cancellation primitive (e.g., `threading.Event`) passed into recording, transcription, model generation, and TTS playback components.

**Rationale:** Creates one consistent cancellation contract and avoids stage-specific ad hoc interruption paths.

**Alternatives considered:**
- Separate cancellation flags per stage: rejected (coordination complexity and race risk).

### 4) Interruption semantics and state safety
`Esc` and `Ctrl+C` will trigger cancellation and immediate transition handling:
- print `[Interrupted]`
- clear/discard in-flight stage output as needed
- return to `[Ready]`

If model requests cannot be physically canceled, the response is ignored when it returns if cancellation is set.

**Rationale:** Guarantees deterministic UX and prevents canceled results from leaking into next state.

### 5) Privacy-safe path/config handling
Machine-specific paths (Whisper model, workspace/temp/audio/transcript paths) move to env/config resolution with safe defaults and sanitized user-facing errors. Internal exceptions may retain detail for debug mode/log sinks, but normal CLI output must avoid absolute local paths.

**Rationale:** Prevents private path disclosure and supports portable local setup.

**Alternatives considered:**
- Keep hardcoded paths and mask only logs: rejected (still brittle and unsafe in code/config).

### 6) Repository hygiene for local artifacts
Add/update `.env.example` and `.gitignore` entries relevant to this project to prevent accidental commits of secrets and local generated data (recordings, transcripts, temp/cache artifacts).

**Rationale:** Reduces privacy/security risk and keeps repository clean.

## Risks / Trade-offs

- [Cancellation races between stage completion and interrupt signal] -> Mitigation: check cancellation flag before publishing each stage result and before state transitions.
- [Esc key capture differences across terminals/platforms] -> Mitigation: support both `Esc` and `Ctrl+C`; keep Ctrl+C as robust baseline.
- [More configuration requirements can increase setup friction] -> Mitigation: provide `.env.example`, clear developer-facing validation errors, and safe optional defaults where possible.
- [Sanitized messages may hide debugging detail for developers] -> Mitigation: keep detailed traces behind debug logging while preserving clean user-facing output.

## Migration Plan

1. Add prompt file and prompt-loading helper; wire pipeline to use file-backed prompt.
2. Add/adjust input loop logic for Enter toggle and interrupt handling.
3. Thread cancellation event through recording/transcription/thinking/speaking stages.
4. Update path/config resolution and sanitize user-facing error output.
5. Update `.env.example` and `.gitignore` for local/sensitive artifacts.
6. Validate end-to-end state transitions and interruption outcomes.

Rollback: revert to previous runtime input/cancellation integration while keeping prompt file additive changes if needed.

## Open Questions

- Which existing module should own cross-stage cancellation orchestration (CLI interface layer vs. pipeline orchestration layer)?
- Should `WHISPER_MODEL_PATH` be required in all environments or optional with project-local discovery fallback?
- Which errors should remain visible in non-debug mode versus redirected to debug logs only?
