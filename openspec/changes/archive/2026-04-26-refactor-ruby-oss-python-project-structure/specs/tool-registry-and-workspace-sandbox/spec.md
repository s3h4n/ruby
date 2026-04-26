## ADDED Requirements

### Requirement: Tool registry controls tool lifecycle and access
The tools layer SHALL provide a registry that supports name-based registration and invocation, checks configured enabled tools, rejects unknown tools, and rejects disabled tools.

#### Scenario: Unknown tool invocation is blocked
- **WHEN** the assistant requests a tool name that is not registered
- **THEN** the registry returns a failure outcome and does not execute any handler

### Requirement: Tool handlers are grouped by responsibility
The system tools `get_time` and `open_app` SHALL be implemented in `ruby/tools/system.py`, and file tools `list_directory`, `create_folder`, and `create_file` SHALL be implemented in `ruby/tools/files.py`.

#### Scenario: Tool modules expose expected handlers
- **WHEN** tool registration initializes
- **THEN** handlers from system and file tool modules are registered under documented tool names

### Requirement: Workspace path resolution enforces sandbox boundaries
The security layer SHALL provide `safe_resolve_workspace_path(workspace_dir, requested_path)` that blocks path traversal and restricts file operations to the configured `ruby_workspace` tree.

#### Scenario: Traversal path is denied
- **WHEN** a file tool requests a path containing `..`
- **THEN** `safe_resolve_workspace_path` rejects the request as invalid

### Requirement: Unsafe absolute and home-expansion paths are denied
The path resolver SHALL reject absolute paths outside the workspace, SHALL reject `~` expansion inputs, and SHALL reject hidden/system-sensitive paths as defined by policy.

#### Scenario: Absolute path outside workspace is denied
- **WHEN** a file tool requests `/tmp/notes.txt` while workspace is `ruby_workspace`
- **THEN** path resolution fails and no file operation is performed
