"""Domain errors used across Ruby modules."""


class RubyError(Exception):
    """Base error for Ruby runtime failures."""


class ConfigError(RubyError):
    """Configuration loading or validation failed."""


class StartupCheckError(RubyError):
    """Startup checks failed before runtime."""


class ProviderError(RubyError):
    """Provider-specific error during STT/LLM/TTS operations."""


class ToolError(RubyError):
    """Tool execution or tool registration error."""


class SafetyError(RubyError):
    """Security policy or permission violation."""
