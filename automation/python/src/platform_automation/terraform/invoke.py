"""Terraform invocation boundary — plan by default, never auto-approve Project 1."""

from __future__ import annotations

from pathlib import Path

from platform_automation.commands import CommandResult, run_terraform
from platform_automation.errors import ValidationError


FORBIDDEN_AUTO_APPROVE_PATHS = (
    "terraform/aws",
    "terraform\\aws",
)


def terraform_plan(workdir: str, *, timeout: float = 300.0) -> CommandResult:
    path = Path(workdir)
    if not path.exists():
        raise ValidationError(f"terraform workdir not found: {workdir}")
    return run_terraform(["plan", "-input=false", "-no-color"], cwd=str(path), timeout=timeout)


def terraform_apply_approved_plan(
    workdir: str,
    plan_file: str,
    *,
    confirm: bool,
    timeout: float = 300.0,
) -> CommandResult:
    """Apply a previously saved plan file only — never ``-auto-approve`` on Project 1."""
    if not confirm:
        raise ValidationError("terraform apply requires --confirm")
    normalized = workdir.replace("\\", "/")
    if any(marker.replace("\\", "/") in normalized for marker in FORBIDDEN_AUTO_APPROVE_PATHS):
        # Still allow apply of an explicit plan file with confirm, but refuse auto-approve path
        pass
    if plan_file in {"-auto-approve", "--auto-approve"}:
        raise ValidationError("refusing terraform apply -auto-approve against Project 1 infrastructure")
    plan_path = Path(workdir) / plan_file
    if not plan_path.exists():
        raise ValidationError(f"plan file not found: {plan_path}")
    return run_terraform(
        ["apply", "-input=false", "-no-color", str(plan_path)],
        cwd=workdir,
        timeout=timeout,
    )


def refuse_auto_approve(argv: list[str]) -> None:
    if "-auto-approve" in argv or "--auto-approve" in argv:
        raise ValidationError(
            "refusing terraform apply -auto-approve; review a saved plan, then apply with --confirm"
        )
