## Context

Ruby currently needs a first working release that is fully local on macOS, but the architecture must not trap the project in a local-only design. The codebase needs clear extension seams for future providers (cloud/local), additional interfaces (text/web/API), and higher-safety tool execution while delivering a usable voice assistant in v1.

Primary constraints for v1 are: no cloud APIs, no browsing, no web server, no destructive tools, and no unrestricted shell execution.

## Goals / Non-Goals

**Goals:**
- Deliver a working local voice assistant loop (wake/listen -> STT -> LLM -> optional tool -> TTS).
- Separate business orchestration from interface and provider implementations.
- Enforce safety boundaries for file and command operations.
- Keep configuration centralized and runtime-selectable by provider name.
- Make future provider and interface additions additive, not rewrite-heavy.

**Non-Goals:**
- Cloud model/provider integration in v1.
- Web browsing/search execution in v1.
- Web UI or local HTTP API server in v1.
- Agentic multi-step planning, memory persistence, or database storage in v1.
- Arbitrary shell execution or delete operations in v1.

## Decisions

1. **Adopt layered package boundaries under `ruby/`**
   - Decision: Keep `core/` as orchestration, `providers/` as adapters, `audio/` as I/O primitives, `tools/` and `security/` for controlled side effects, and `interfaces/` for user entrypoints.
   - Rationale: Prevents business logic from leaking into voice loop code and keeps future interfaces reusable.
   - Alternative considered: Single monolithic app loop; rejected due to tight coupling and poor future extensibility.

2. **Use provider base contracts and config-driven implementation selection**
   - Decision: Define `STTProvider`, `LLMProvider`, and `TTSProvider` interfaces and implement local adapters (`whisper_cpp`, `ollama`, `kokoro`).
   - Rationale: Enables cloud/local swaps later without changing `core.assistant` behavior.
   - Alternative considered: Direct calls to whisper/Ollama/Kokoro from main loop; rejected because it blocks provider portability.

3. **Use strict structured LLM outputs with response-type routing**
   - Decision: Parse LLM output into `answer`, `tool_call`, or `intent` response objects; execute only supported types.
   - Rationale: Makes tool execution deterministic and safe, and creates a clear hook for future intent routing.
   - Alternative considered: Free-form text tool extraction; rejected due to high ambiguity and safety risk.

4. **Centralize tool execution through a registry plus policy checks**
   - Decision: Each tool has metadata (name, description, args, risk, enabled) and a single execution path with permission checks.
   - Rationale: Allows controlled growth of tool surface and consistent auditing/confirmation behavior.
   - Alternative considered: Hardcoded `if/else` tool handlers; rejected because it scales poorly and weakens safety controls.

5. **Sandbox file operations to `ruby_workspace/` and disable shell by default**
   - Decision: Implement path resolution guards and traversal prevention for file tools; keep shell executor present but disabled with allowlist/denylist scaffolding.
   - Rationale: Delivers useful local operations while minimizing accidental or malicious system impact.
   - Alternative considered: System-wide file and shell access with prompt warnings; rejected as too risky for v1.

6. **Implement fail-fast startup checks with actionable remediation**
   - Decision: Validate config, required directories, whisper binary/model, Ollama reachability, Kokoro import, and microphone readiness at startup.
   - Rationale: Reduces silent runtime failures and improves operator ergonomics.
   - Alternative considered: Lazy checks at first use; rejected due to poor UX and harder debugging.

## Risks / Trade-offs

- [Wake-word reliability varies across environments] -> Provide push-to-talk/manual trigger fallback and tunable threshold/chunk settings.
- [Strict JSON contracts can fail on malformed model output] -> Add robust parsing, fallback user message, and prompt reinforcement.
- [Sandbox restrictions may feel limiting] -> Document boundaries clearly and define future safe-expansion path.
- [macOS-specific behavior reduces portability] -> Keep platform-specific logic isolated in tool/audio adapters.
- [Local model latency on low-end hardware] -> Keep responses short, keep recording windows modest, and allow model config tuning.

## Migration Plan

1. Add the new package structure and root runner while preserving simple startup command (`python app.py`).
2. Introduce config loading and startup validation before entering runtime loop.
3. Implement provider adapters and connect them via core pipeline APIs.
4. Add registry-based tools and security policies with safe defaults.
5. Validate end-to-end with sample commands and document operational troubleshooting.
6. Future upgrades (cloud/search/web/API) should register additional adapters and interfaces without modifying core contracts.

Rollback strategy: if runtime stability issues arise, disable tool execution and wake-word mode via config while preserving local Q&A voice flow.

## Open Questions

- Which wake-word engine/library will be used in practice for best local macOS reliability?
- Should medium/high-risk confirmations be voice-confirmed, CLI-confirmed, or both by default?
- What minimum schema validation strategy should be used for tool args in v1 (manual checks vs. optional pydantic)?
