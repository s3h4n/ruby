"""Module execution entrypoint for `python -m ruby`."""

from __future__ import annotations

from ruby.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
