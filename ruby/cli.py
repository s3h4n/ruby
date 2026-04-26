"""Public CLI entrypoint for Ruby command routing."""

from __future__ import annotations

from ruby.interfaces.cli import (
    AVAILABLE_COMMANDS,
    config_command,
    dispatch_command,
    doctor_command,
    init_command,
    main,
    models_command,
    run_command,
)

__all__ = [
    "AVAILABLE_COMMANDS",
    "config_command",
    "dispatch_command",
    "doctor_command",
    "init_command",
    "main",
    "models_command",
    "run_command",
]
