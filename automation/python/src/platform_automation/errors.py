"""Typed automation exceptions and CLI exit codes."""

from __future__ import annotations


class AutomationError(Exception):
    """Base error for platform automation."""

    exit_code = 1


class ConfigurationError(AutomationError):
    """Invalid or missing configuration."""

    exit_code = 2


class ValidationError(AutomationError):
    """Input failed validation before calling external systems."""

    exit_code = 3


class CommandError(AutomationError):
    """External command failed (kubectl, aws, ansible-playbook, terraform)."""

    exit_code = 4

    def __init__(
        self,
        message: str,
        *,
        returncode: int | None = None,
        stdout: str = "",
        stderr: str = "",
    ) -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class APIError(AutomationError):
    """REST / cloud / Kubernetes API error."""

    exit_code = 5

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class AutomationTimeoutError(AutomationError):
    """Operation exceeded its deadline.

    Named distinctly from built-in ``TimeoutError``; re-exported as
    ``TimeoutError`` from this module for the Section 24 vocabulary.
    """

    exit_code = 6


TimeoutError = AutomationTimeoutError  # noqa: A001 — intentional alias for lab docs


class AuthenticationError(AutomationError):
    """Missing or invalid credentials / kubeconfig / AWS identity."""

    exit_code = 7


def exit_code_for(exc: BaseException) -> int:
    if isinstance(exc, AutomationError):
        return exc.exit_code
    return 1
