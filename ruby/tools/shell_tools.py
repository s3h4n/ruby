"""Shell tool scaffolding with strict policy checks."""

from __future__ import annotations

import subprocess

from ruby.security.command_policy import CommandPolicy


class ShellTools:
    """Future-ready shell execution tool (disabled by default)."""

    def __init__(self, policy: CommandPolicy) -> None:
        self.policy = policy

    def run_command(self, args: dict[str, object]) -> str:
        command = str(args.get("command", "")).strip()
        if not command:
            return "Missing 'command' argument."

        allowed, reason = self.policy.validate(command)
        if not allowed:
            return f"Shell command denied: {reason}"

        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        output = result.stdout.strip() or result.stderr.strip()
        if result.returncode != 0:
            return f"Shell command failed ({result.returncode}): {output}"
        return output or "Command executed successfully."
