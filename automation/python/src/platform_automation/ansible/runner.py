"""Invoke Ansible via ansible-runner (Linux) or ansible-playbook subprocess (Windows)."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from platform_automation.commands import run_command
from platform_automation.errors import CommandError, ValidationError
from platform_automation.logging import redact


@dataclass
class PlaybookResult:
    rc: int
    status: str
    events: list[dict[str, Any]] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    duration: float = 0.0
    backend: str = "subprocess"

    @property
    def ok(self) -> bool:
        return self.rc == 0 and self.status in {"successful", "success"}


def _runner_available() -> bool:
    if sys.platform.startswith("win"):
        return False
    try:
        import ansible_runner  # noqa: F401

        return True
    except Exception:
        return False


def run_playbook(
    playbook: str,
    *,
    inventory: str | None = None,
    extravars: dict[str, Any] | None = None,
    cwd: str | None = None,
    timeout: float | None = 600.0,
    tags: list[str] | None = None,
    check: bool = False,
    diff: bool = False,
) -> PlaybookResult:
    playbook_path = Path(playbook)
    if not playbook_path.exists():
        raise ValidationError(f"playbook not found: {playbook}")

    if _runner_available():
        return _run_with_runner(
            playbook_path,
            inventory=inventory,
            extravars=extravars,
            cwd=cwd,
            timeout=timeout,
            tags=tags,
            check=check,
            diff=diff,
        )
    return _run_with_subprocess(
        playbook_path,
        inventory=inventory,
        extravars=extravars,
        cwd=cwd,
        timeout=timeout,
        tags=tags,
        check=check,
        diff=diff,
    )


def _run_with_runner(
    playbook_path: Path,
    *,
    inventory: str | None,
    extravars: dict[str, Any] | None,
    cwd: str | None,
    timeout: float | None,
    tags: list[str] | None,
    check: bool,
    diff: bool,
) -> PlaybookResult:
    import ansible_runner

    started = time.monotonic()
    kwargs: dict[str, Any] = {
        "private_data_dir": cwd or str(playbook_path.parent.parent),
        "playbook": str(playbook_path),
        "quiet": True,
    }
    if inventory:
        kwargs["inventory"] = inventory
    if extravars:
        kwargs["extravars"] = extravars
    if tags:
        kwargs["tags"] = tags
    if check:
        kwargs["cmdline"] = "--check" + (" --diff" if diff else "")
    elif diff:
        kwargs["cmdline"] = "--diff"
    if timeout:
        kwargs["timeout"] = int(timeout)

    runner = ansible_runner.run(**kwargs)
    events = []
    for event in runner.events or []:
        # Redact potential secrets in event strings
        safe = {k: redact(str(v)) if isinstance(v, str) else v for k, v in event.items()}
        events.append(safe)
    status = str(runner.status or "unknown")
    rc = int(runner.rc if runner.rc is not None else 1)
    return PlaybookResult(
        rc=rc,
        status=status if status != "successful" else "successful",
        events=events,
        stdout=redact(str(getattr(runner, "stdout", "") or "")),
        stderr="",
        duration=time.monotonic() - started,
        backend="ansible-runner",
    )


def _run_with_subprocess(
    playbook_path: Path,
    *,
    inventory: str | None,
    extravars: dict[str, Any] | None,
    cwd: str | None,
    timeout: float | None,
    tags: list[str] | None,
    check: bool,
    diff: bool,
) -> PlaybookResult:
    argv = ["ansible-playbook", str(playbook_path)]
    if inventory:
        argv.extend(["-i", inventory])
    if check:
        argv.append("--check")
    if diff:
        argv.append("--diff")
    if tags:
        argv.extend(["--tags", ",".join(tags)])
    if extravars:
        for key, value in extravars.items():
            argv.extend(["-e", f"{key}={value}"])

    try:
        result = run_command(argv, timeout=timeout, check=False, cwd=cwd)
    except CommandError as exc:
        return PlaybookResult(
            rc=exc.returncode or 1,
            status="timeout" if "timed out" in str(exc).lower() else "failed",
            stdout=redact(exc.stdout),
            stderr=redact(exc.stderr),
            duration=0.0,
            backend="subprocess",
        )
    status = "successful" if result.returncode == 0 else "failed"
    return PlaybookResult(
        rc=result.returncode,
        status=status,
        stdout=redact(result.stdout),
        stderr=redact(result.stderr),
        duration=result.duration,
        backend="subprocess",
    )


def get_status(result: PlaybookResult) -> str:
    return result.status


def get_events(result: PlaybookResult) -> list[dict[str, Any]]:
    return list(result.events)


def get_artifacts(result: PlaybookResult) -> dict[str, Any]:
    return {
        "rc": result.rc,
        "status": result.status,
        "duration": result.duration,
        "backend": result.backend,
        "stdout_preview": result.stdout[:500],
        "stderr_preview": result.stderr[:500],
    }
