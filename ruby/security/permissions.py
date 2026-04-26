"""Permission and path-sandbox enforcement."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ruby.config.settings import SecurityConfig
from ruby.security.paths import safe_resolve_workspace_path


ConfirmCallback = Callable[[str], bool]


class WorkspaceGuard:
    """Guarantees file operations stay inside configured workspace."""

    def __init__(self, workspace_dir: Path) -> None:
        self.workspace_dir = workspace_dir.resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def safe_path(self, relative_path: str) -> Path:
        return safe_resolve_workspace_path(self.workspace_dir, relative_path)


class RiskPermissionPolicy:
    """Applies confirmation rules by risk level."""

    def __init__(
        self,
        security_config: SecurityConfig,
        confirm_callback: ConfirmCallback | None = None,
    ) -> None:
        self.security_config = security_config
        self.confirm_callback = confirm_callback

    def allow(self, risk_level: str, action_name: str) -> bool:
        if risk_level == "low":
            return True

        if risk_level == "medium" and self.security_config.require_confirmation_for_medium_risk:
            if self.confirm_callback is None:
                return False
            return self.confirm_callback(f"Allow medium-risk action '{action_name}'?")

        if risk_level == "high" and self.security_config.require_confirmation_for_high_risk:
            if self.confirm_callback is None:
                return False
            return self.confirm_callback(f"Allow high-risk action '{action_name}'?")

        return True
