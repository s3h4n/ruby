"""Root runner that delegates to Ruby CLI interface."""

from ruby.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
