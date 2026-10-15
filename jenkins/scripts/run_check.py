"""Run one pipeline check and report an honest status.

Usage:
    run_check.py --name ruff --required [--cwd DIR] [--timeout SECONDS]
                 [--install-hint TEXT] [--summary-file PATH] -- ruff check src

Exit codes:
    0   PASSED   - the command exited 0
    1   FAILED   - the command exited non-zero or timed out
    2   MISSING  - a required tool is not installed (configuration error)
    78  SKIPPED  - an optional tool is not installed; callers must surface this
                   (Jenkins marks the build UNSTABLE), never treat it as a pass

The command is executed without a shell. Standard library only, so it runs
before the automation virtualenv exists.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

PASSED = 0
FAILED = 1
MISSING = 2
SKIPPED = 78


def _report(summary_file: str | None, name: str, status: str, detail: str) -> None:
    line = f"[check] {name}: {status}" + (f" - {detail}" if detail else "")
    print(line, flush=True)
    if summary_file:
        path = Path(summary_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def run_check(
    name: str,
    command: list[str],
    *,
    required: bool,
    cwd: str | None = None,
    timeout: float | None = None,
    install_hint: str = "",
    summary_file: str | None = None,
) -> int:
    if not command:
        _report(summary_file, name, "FAILED", "no command given")
        return FAILED
    if shutil.which(command[0]) is None:
        hint = f" Install: {install_hint}" if install_hint else ""
        if required:
            _report(
                summary_file,
                name,
                "MISSING REQUIRED TOOL",
                f"'{command[0]}' is not on PATH; this check cannot pass without it.{hint}",
            )
            return MISSING
        _report(
            summary_file,
            name,
            "SKIPPED (optional tool not installed)",
            f"'{command[0]}' is not on PATH; this check did NOT run.{hint}",
        )
        return SKIPPED

    started = time.monotonic()
    try:
        completed = subprocess.run(command, cwd=cwd, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        _report(summary_file, name, "FAILED", f"timed out after {timeout:g}s")
        return FAILED
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        _report(summary_file, name, "FAILED", f"exit {completed.returncode} after {elapsed:.1f}s")
        return FAILED
    _report(summary_file, name, "PASSED", f"{elapsed:.1f}s")
    return PASSED


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--" not in argv:
        print("run_check.py: missing '--' before the command", file=sys.stderr)
        return MISSING
    split = argv.index("--")
    parser = argparse.ArgumentParser(prog="run_check.py")
    parser.add_argument("--name", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--required", action="store_true")
    mode.add_argument("--optional", action="store_true")
    parser.add_argument("--cwd", default=None)
    parser.add_argument("--timeout", type=float, default=None)
    parser.add_argument("--install-hint", default="")
    parser.add_argument("--summary-file", default=None)
    args = parser.parse_args(argv[:split])
    return run_check(
        args.name,
        argv[split + 1 :],
        required=args.required,
        cwd=args.cwd,
        timeout=args.timeout,
        install_hint=args.install_hint,
        summary_file=args.summary_file,
    )


if __name__ == "__main__":
    sys.exit(main())
