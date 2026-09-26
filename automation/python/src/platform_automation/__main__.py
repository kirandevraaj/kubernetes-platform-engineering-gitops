"""Allow ``python -m platform_automation``."""

from platform_automation.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
