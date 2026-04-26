"""Shell command policy scaffolding (disabled by default in v1)."""

from __future__ import annotations

from dataclasses import field

from ruby.core.compat import compat_dataclass


@compat_dataclass(slots=True)
class CommandPolicy:
    """Defines allowlist/denylist behavior for future shell tools."""

    shell_enabled: bool = False
    allowlist: set[str] = field(default_factory=set)
    denylist_fragments: set[str] = field(
        default_factory=lambda: {
            "rm -rf",
            "sudo",
            "chmod -R",
            "chown -R",
            "diskutil",
            "mkfs",
            "dd",
            "killall",
            "launchctl unload",
        }
    )

    def validate(self, command: str) -> tuple[bool, str]:
        normalized = command.strip()
        if not self.shell_enabled:
            return False, "Shell command execution is disabled in v1."

        lowered = normalized.lower()
        for fragment in self.denylist_fragments:
            if fragment.lower() in lowered:
                return False, f"Command contains blocked fragment: {fragment}"

        if self.allowlist and normalized.split(" ")[0] not in self.allowlist:
            return False, "Command is not in allowlist."

        return True, "Allowed"
