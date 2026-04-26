## Context

Ruby is currently local-first but not open-source friendly because model/runtime selection is effectively fixed in configuration defaults and startup assumptions. New users need an initialization workflow that can discover local dependencies (`whisper.cpp`, whisper models, Ollama models), bootstrap project files (`config.json`, `.env`), and validate runtime health before `run`.

Key constraints:
- v1 remains local-first (`whisper.cpp`, Ollama, Kokoro, openWakeWord path retained).
- API keys and cloud secrets MUST stay out of `config.json`.
- Safety boundaries MUST remain strict (workspace-only file tools, shell disabled by default, no destructive commands).
- Existing users should not lose the current `python app.py` run path.

## Goals / Non-Goals

**Goals:**
- Add command dispatcher with `init`, `run`, `doctor`, `models`, and `config` commands (`run` default).
- Add first-run init wizard that discovers/selects whisper and Ollama models and writes non-secret config.
- Add provider-ready abstractions for STT/LLM/TTS with local defaults and future cloud extension seams.
- Add doctor diagnostics that provide clear pass/fail remediation.
- Add open-source onboarding docs and repository hygiene (`requirements.txt`, `.gitignore`, `.env.example`).
- Preserve secure-by-default behavior and avoid secret leakage.

**Non-Goals:**
- Implement full cloud-provider production integrations in this change (OpenRouter remains disabled placeholder).
- Auto-build `whisper.cpp` by default.
- Enable unrestricted shell tooling or destructive file operations.
- Ship custom wake-word model training.

## Decisions

1. **Command-based app entrypoint with backward-compatible default**
   - Decision: `app.py` will parse optional command and route to dedicated handlers; no command defaults to `run`.
   - Rationale: Enables explicit operational lifecycle (`init`, `doctor`, etc.) while preserving current user behavior.
   - Alternatives considered:
     - Separate scripts (`ruby-init`, `ruby-doctor`): rejected due to more packaging friction.
     - Interactive menu always: rejected because it slows scripted usage.

2. **Dedicated setup package for init/model/doctor concerns**
   - Decision: Introduce `ruby/setup/init_wizard.py`, `ruby/setup/model_discovery.py`, and `ruby/setup/doctor.py`.
   - Rationale: Keeps setup/ops concerns out of core runtime and keeps modules testable.
   - Alternatives considered:
     - Keep all logic in CLI module: rejected due to coupling and maintainability cost.

3. **Provider-ready interfaces with local-first defaults**
   - Decision: Define stable interfaces in `ruby/providers/*/base.py` and instantiate providers from config/env factory logic.
   - Rationale: Supports immediate local use while keeping future OpenRouter/cloud enablement low-risk.
   - Alternatives considered:
     - Keep direct Ollama/Whisper calls in pipeline: rejected; blocks future providers.

4. **Secrets in `.env`, non-secrets in `config.json`**
   - Decision: Load env via `python-dotenv`; generate `.env` from `.env.example` when missing; keep provider keys only in env.
   - Rationale: Open-source safety and predictable secret handling.
   - Alternatives considered:
     - Store optional keys in config: rejected due to accidental commit risk.

5. **Safe subprocess model operations with strict allowlists**
   - Decision: Any model download/pull helper uses non-shell subprocess invocations with hardcoded allowlisted model names and explicit workdir.
   - Rationale: Prevents command injection and keeps setup UX smooth.
   - Alternatives considered:
     - Accept arbitrary model strings: rejected due to security risk.

6. **Doctor as structured health report with remediation output**
   - Decision: `doctor` performs check suite (packages, binaries, models, provider connectivity, Kokoro import, mic access) and prints deterministic pass/fail lines with next actions.
   - Rationale: Reduces onboarding support burden for open-source users.
   - Alternatives considered:
     - Fail fast on first error only: rejected because users benefit from full report in one run.

7. **Compatibility via migration-or-guidance strategy**
   - Decision: On legacy config mismatch, system attempts lightweight migration where deterministic; otherwise prints explicit `python app.py init` guidance.
   - Rationale: Avoids silently breaking existing installs.
   - Alternatives considered:
     - Hard fail unconditionally: rejected due to poor upgrade UX.

## Risks / Trade-offs

- **[Init wizard complexity growth]** → Mitigation: keep wizard steps modular and unit-test discovery/util helpers.
- **[Ollama unavailable during init]** → Mitigation: show clear instructions (`ollama serve`) and offer provider-selection path.
- **[User confusion between config and env]** → Mitigation: enforce non-secret config printout and README examples.
- **[Cross-platform assumptions in diagnostics]** → Mitigation: scope checks to macOS-first behavior and label platform-specific guidance.
- **[Optional auto-pull/download may fail offline]** → Mitigation: make pull/download opt-in and keep manual instructions always visible.

## Migration Plan

1. Introduce command dispatcher and preserve default `run` path.
2. Add setup/doctor/model discovery modules and integrate into CLI commands.
3. Add provider factory/env loading updates and OpenRouter placeholder module.
4. Add file generation flow for `.env.example`/`.env` and config bootstrap.
5. Add compatibility detection for older config and migration/guidance path.
6. Update docs, dependency manifests, and `.gitignore`.
7. Verify with smoke flows for fresh setup and existing config users.

Rollback strategy:
- Revert to previous app entrypoint and existing static config behavior by rolling back this change set if command or provider routing causes blocking regressions.

## Open Questions

- Should optional Ollama auto-pull be included in this change by default, or deferred behind a secondary prompt only?
- Should legacy config migration mutate file in place, or write migrated output and ask user confirmation before replacing?
- Should `doctor` return distinct non-zero exit codes per failed check category for automation, or a single failure code in v1?
