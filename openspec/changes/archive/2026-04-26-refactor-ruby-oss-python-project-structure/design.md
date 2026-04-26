## Context

Ruby is currently a local Python voice assistant that already works with Whisper (via `whisper.cpp`), Ollama, Kokoro, and openWakeWord, but the codebase layout is mixed and difficult to maintain as an OSS project. Runtime and local-machine artifacts (`recordings/`, `responses/`, `ruby_workspace/`, `whisper.cpp/`, `.env`) are intentionally local and should remain untracked. The refactor must preserve current command behavior while introducing clear module boundaries and contributor-facing documentation.

Constraints:
- Preserve working commands (`python app.py run`, `python app.py init`, `python app.py doctor`, `python -m ruby run`).
- Do not introduce unrelated functionality.
- Maintain local-first provider defaults (Whisper + Ollama + Kokoro) and keep OpenRouter non-default.
- Keep secure workspace file handling for tool operations.

## Goals / Non-Goals

**Goals:**
- Establish a clean package architecture under `ruby/` with clear ownership by domain.
- Standardize execution entry points through a thin root runner and package CLI module.
- Centralize configuration, environment loading, and project-root-relative path resolution.
- Define explicit provider interfaces and separate implementation modules for STT/LLM/TTS.
- Formalize tool registry behavior and workspace path sandboxing.
- Add minimal but meaningful tests and docs required for OSS onboarding.

**Non-Goals:**
- Changing fundamental assistant behavior, conversation flow, or model-selection logic beyond structural needs.
- Adding remote/cloud capabilities as defaults.
- Introducing heavy packaging/release automation (wheel publishing, CI pipelines) in this change.

## Decisions

### 1) Monolithic script split into domain package modules
- Decision: Move business logic from root-level script modules into `ruby/` package domains (`core`, `audio`, `providers`, `tools`, `security`, `setup`, `config`).
- Rationale: Improves maintainability and makes responsibilities explicit for contributors.
- Alternatives considered:
  - Keep a flat module structure at repo root: rejected because ownership remains unclear.
  - Perform incremental partial split: rejected because it prolongs mixed architecture and migration overhead.

### 2) Keep root `app.py` as compatibility runner
- Decision: Root `app.py` only calls `ruby.cli.main`, and `ruby/__main__.py` invokes the same `main`.
- Rationale: Preserves existing usage while enabling `python -m ruby` UX.
- Alternatives considered:
  - Remove `app.py` and force module execution: rejected to avoid breaking existing workflows.

### 3) Centralized settings loader with OSS-safe tracked defaults
- Decision: Implement settings loading in `ruby/config/settings.py`, with precedence: `config.json` (if present) then `config.example.json`; load `.env` via `python-dotenv` when available.
- Rationale: Ensures deterministic config behavior while protecting secret and local-machine data.
- Alternatives considered:
  - Track `config.json` directly: rejected for OSS safety and environment drift concerns.
  - Environment-only config: rejected because current project already relies on JSON config shape.

### 4) Provider interface contracts with local-first defaults
- Decision: Introduce base contracts for STT/LLM/TTS and relocate provider implementations to typed module paths, including disabled OpenRouter placeholder.
- Rationale: Decouples assistant core from provider details and simplifies adding future providers.
- Alternatives considered:
  - Keep direct provider calls in assistant flow: rejected due to tight coupling.

### 5) Tool registry gatekeeping + explicit workspace sandbox
- Decision: Route tool execution through `ruby/tools/registry.py`, enforce enabled-tool checks, and use `ruby/security/paths.py` for safe workspace path resolution.
- Rationale: Reduces accidental unsafe operations and creates testable policy boundaries.
- Alternatives considered:
  - Keep ad hoc tool invocation with per-tool checks: rejected because policy drift is likely.

### 6) Minimum OSS readiness bundle in same change
- Decision: Include README rewrite, docs (`architecture.md`, `security.md`, `providers.md`), `scripts/setup_dev.sh`, cleaned `requirements.txt`, `.env.example`, `config.example.json`, and baseline tests.
- Rationale: Structural refactor without docs/tests leaves the project difficult for external contributors.

## Risks / Trade-offs

- [Risk] Import-path regressions during module moves -> Mitigation: keep compatibility entry points and add smoke checks in `doctor` plus tests for critical contracts.
- [Risk] Runtime dependency behavior differs across dev machines -> Mitigation: `doctor` validates imports, folders, binaries, model presence, and selected provider availability.
- [Risk] Overly strict path validation blocks valid workspace operations -> Mitigation: define explicit policy and add tests for both allowed and blocked path patterns.
- [Trade-off] More files and modules increase initial navigation overhead -> Mitigation: add architecture docs and consistent package naming.

## Migration Plan

1. Introduce package scaffolding and compatibility entry points (`app.py`, `ruby/__main__.py`, CLI router).
2. Move config handling and path utilities first to stabilize dependencies for other modules.
3. Extract provider abstractions and assistant core orchestration.
4. Move audio/setup/tool logic into dedicated modules and wire through registry/security boundaries.
5. Update ignore rules, requirements, examples, docs, and tests.
6. Run validation (`doctor`, command smoke runs, pytest) to confirm behavior parity.

Rollback strategy:
- If parity breaks, restore previous `app.py`-centric execution from prior commit and re-apply refactor incrementally by domain.

## Open Questions

- Should `config` command print a redacted merged runtime view or only indicate file/env sources used?
- Should OpenRouter placeholder include a concrete response schema example now, or remain strict error-only until activation support is added?
