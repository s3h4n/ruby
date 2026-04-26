"""Safe system-level tools for v1."""

from __future__ import annotations

import datetime as dt
import subprocess


class SystemTools:
    """System actions with explicit safety boundaries."""

    def __init__(self, allowed_apps: dict[str, str]) -> None:
        self.allowed_apps = {key.lower(): value for key, value in allowed_apps.items()}

    def get_time(self, args: dict[str, object]) -> str:
        _ = args
        now = dt.datetime.now().strftime("%I:%M %p")
        return f"It is {now}."

    def open_app(self, args: dict[str, object]) -> str:
        raw_name = str(args.get("app", "")).strip().lower()
        if not raw_name:
            return "No app name was provided."

        app_name = self.allowed_apps.get(raw_name)
        if app_name is None:
            return f"App '{raw_name}' is not in the allowed app list."

        result = subprocess.run(["open", "-a", app_name], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "unknown error"
            return f"Failed to open {app_name}: {stderr}"
        return f"Opened {app_name}."
