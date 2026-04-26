# Security Model

Ruby defaults to a local-safe posture and explicit opt-in for risky behavior.

## Path and Workspace Safety

- File tools are restricted to `ruby_workspace/`.
- `safe_resolve_workspace_path()` blocks:
  - parent traversal (`..`)
  - paths outside workspace root
  - home-expansion inputs (`~`)
  - hidden path segments in v1

## Tool Execution Guardrails

- Every tool is registered with risk metadata and enabled/disabled state.
- Unknown tools are rejected with a structured `ToolResult` failure.
- Disabled tools are rejected even if requested.
- Medium/high-risk tool execution requires confirmation when configured.

## Command Policy

- Shell command execution is disabled by default.
- Shell tooling uses centralized command policy checks for explicit restrictions.

## Secrets and Configuration Hygiene

- Secrets are loaded from `.env`; `.env` is ignored by git.
- `config.json` is treated as local machine configuration and ignored by git.
- `config.example.json` and `.env.example` are tracked onboarding templates.
- Inline secret-like fields in config payloads are rejected.
