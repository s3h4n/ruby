## 1. Project Structure and Configuration

- [x] 1.1 Create the `ruby/` package layout (`core`, `audio`, `providers`, `tools`, `security`, `interfaces`, `config`) with `__init__.py` files
- [x] 1.2 Add root `app.py` that delegates startup to `ruby.interfaces.cli.main`
- [x] 1.3 Create/update `config.json` with assistant, provider, audio, security, and tools sections matching v1 local defaults
- [x] 1.4 Ensure runtime folders (`recordings/`, `responses/`, `ruby_workspace/`) are created or validated at startup

## 2. Core Assistant Pipeline

- [x] 2.1 Implement shared schemas and error types for assistant responses (`answer`, `tool_call`, `intent`) and runtime failures
- [x] 2.2 Implement `ruby.core.assistant` with `handle_text(text: str)` and `handle_audio(audio_path: str)` entrypoints
- [x] 2.3 Implement `ruby.core.pipeline` orchestration for STT -> LLM -> optional tool -> TTS flow
- [x] 2.4 Add intent fallback handling that returns "That intent is not implemented yet." for unsupported intents
- [x] 2.5 Add local-safe system prompt builder enforcing JSON-only output and v1 tool/safety constraints

## 3. Provider Abstractions and Local Implementations

- [x] 3.1 Define base interfaces for STT, LLM, and TTS providers under `ruby/providers/*/base.py`
- [x] 3.2 Implement `WhisperCppSTTProvider` using configured whisper.cpp binary and model paths
- [x] 3.3 Implement `OllamaLLMProvider` using configured local Ollama chat API endpoint and model
- [x] 3.4 Implement `KokoroTTSProvider` for local synthesis output compatible with macOS playback
- [x] 3.5 Add provider factory/selection logic driven by `config.json` provider names
- [x] 3.6 Add disabled-by-default search provider placeholders (`ruby/providers/search/base.py`, `web_search_placeholder.py`)

## 4. Audio and CLI Interface

- [x] 4.1 Implement audio recorder/player modules for command capture and `afplay`-based response playback
- [x] 4.2 Implement wake handling module with configurable threshold/chunk parameters and enable flag
- [x] 4.3 Implement CLI main loop that handles wake-driven capture and delegates all processing to core assistant
- [x] 4.4 Add push-to-talk/manual fallback mode when wake detection is disabled or unavailable
- [x] 4.5 Print startup guidance: "Ruby is ready. Say the wake word, then speak your command."

## 5. Tooling and Security Guardrails

- [x] 5.1 Implement central tool registry with metadata fields (name, description, args, risk, enabled, handler)
- [x] 5.2 Implement v1 safe tools: `get_time`, `open_app`, `list_directory`, `create_folder`, and `create_file`
- [x] 5.3 Implement workspace path resolver/validator that blocks traversal and all operations outside `ruby_workspace/`
- [x] 5.4 Implement allowlisted `open_app` behavior from config aliases and reject unknown app names
- [x] 5.5 Create shell tool scaffolding and command policy module with shell disabled by default plus denylist examples
- [x] 5.6 Ensure dangerous requests (e.g., `rm -rf`, `sudo`, system modification attempts) are refused as unsupported in v1

## 6. Startup Validation, Documentation, and Verification

- [x] 6.1 Implement startup checks for config file, whisper binary/model, Ollama API reachability, Kokoro import, and microphone readiness
- [x] 6.2 Add clear remediation messages for each startup failure mode
- [x] 6.3 Write comprehensive `README.md` covering capabilities, setup, run flow, safety model, and future extension guides
- [x] 6.4 Run an end-to-end smoke test with expected commands (time, app open, workspace list, folder create, file create)
- [x] 6.5 Verify refusal behavior for unsupported/dangerous requests and document observed behavior
