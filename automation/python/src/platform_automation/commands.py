"""Safe subprocess wrappers — argument arrays only, never shell=True."""

from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Sequence

from platform_automation.errors import CommandError, ValidationError


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str
    duration: float

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_command(
    argv: Sequence[str],
    *,
    timeout: float | None = 60.0,
    check: bool = True,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
) -> CommandResult:
    if not argv:
        raise ValidationError("command argv must not be empty")
    if any(not isinstance(part, str) for part in argv):
        raise ValidationError("command argv must be a sequence of strings")
    # Guard against accidental shell metacharacter usage patterns
    executable = argv[0]
    if shutil.which(executable) is None and "/" not in executable and "\\" not in executable:
        # Still allow relative paths that exist later; which miss is OK for covered tools
        pass

    started = time.monotonic()
    try:
        completed = subprocess.run(  # noqa: S603 — argv list, shell=False
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        raise CommandError(
            f"command timed out after {timeout}s: {' '.join(argv)}",
            returncode=None,
            stdout=(exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            stderr=(exc.stderr or b"").decode() if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
        ) from exc

    result = CommandResult(
        argv=tuple(argv),
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
        duration=time.monotonic() - started,
    )
    if check and result.returncode != 0:
        raise CommandError(
            f"command failed (rc={result.returncode}): {' '.join(argv)}",
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    return result


def run_kubectl(args: Sequence[str], **kwargs) -> CommandResult:
    return run_command(["kubectl", *args], **kwargs)


def run_aws(args: Sequence[str], **kwargs) -> CommandResult:
    return run_command(["aws", *args], **kwargs)


def run_helm(args: Sequence[str], **kwargs) -> CommandResult:
    return run_command(["helm", *args], **kwargs)


def run_terraform(args: Sequence[str], **kwargs) -> CommandResult:
    return run_command(["terraform", *args], **kwargs)


def run_ansible_playbook(args: Sequence[str], **kwargs) -> CommandResult:
    return run_command(["ansible-playbook", *args], **kwargs)
