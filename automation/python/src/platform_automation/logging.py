"""Structured logging helpers. Never log secrets."""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from typing import Any

_SECRET_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "apikey",
        "api_key",
        "authorization",
        "access_key",
        "secret_key",
        "aws_secret_access_key",
        "aws_session_token",
        "kubeconfig",
        "private_key",
        "client_secret",
    }
)
_REDACT = "***REDACTED***"
_SECRET_PATTERN = re.compile(
    r"(?i)(password|secret|token|api[_-]?key|authorization)\s*[:=]\s*\S+"
)


class StructuredFormatter(logging.Formatter):
    """Emit JSON-ish structured lines with standard fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "component": getattr(record, "component", record.name),
            "operation": getattr(record, "operation", "-"),
            "target": getattr(record, "target", "-"),
            "duration": getattr(record, "duration", None),
            "result": getattr(record, "result", None),
            "message": record.getMessage(),
        }
        # Drop None duration/result for quieter lines
        if payload["duration"] is None:
            del payload["duration"]
        if payload["result"] is None:
            del payload["result"]
        return json.dumps(payload, default=str)


def _scrub_value(key: str, value: Any) -> Any:
    if key.lower() in _SECRET_KEYS or any(s in key.lower() for s in _SECRET_KEYS):
        return _REDACT
    if isinstance(value, str):
        return _SECRET_PATTERN.sub(r"\1=***REDACTED***", value)
    if isinstance(value, dict):
        return {k: _scrub_value(str(k), v) for k, v in value.items()}
    return value


def scrub(data: dict[str, Any] | None) -> dict[str, Any]:
    """Return a copy with secret-like keys redacted."""
    if not data:
        return {}
    return {k: _scrub_value(str(k), v) for k, v in data.items()}


def redact(text: str) -> str:
    """Redact secret-like substrings from free-form text."""
    return _SECRET_PATTERN.sub(r"\1=***REDACTED***", text)


def setup_logging(*, verbose: bool = False, quiet: bool = False) -> logging.Logger:
    """Configure root package logger."""
    logger = logging.getLogger("platform_automation")
    logger.handlers.clear()
    logger.propagate = False
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name or "platform_automation")


class OperationLogger:
    """Context manager that logs start/end with duration."""

    def __init__(
        self,
        operation: str,
        *,
        component: str = "platform",
        target: str = "-",
        logger: logging.Logger | None = None,
    ) -> None:
        self.operation = operation
        self.component = component
        self.target = target
        self.logger = logger or get_logger()
        self._start = 0.0
        self.result = "ok"

    def __enter__(self) -> OperationLogger:
        self._start = time.perf_counter()
        self.logger.info(
            "start",
            extra={
                "component": self.component,
                "operation": self.operation,
                "target": self.target,
                "result": "start",
            },
        )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        duration = round(time.perf_counter() - self._start, 4)
        if exc is not None:
            self.result = "error"
            self.logger.error(
                str(exc),
                extra={
                    "component": self.component,
                    "operation": self.operation,
                    "target": self.target,
                    "duration": duration,
                    "result": "error",
                },
            )
        else:
            self.logger.info(
                "done",
                extra={
                    "component": self.component,
                    "operation": self.operation,
                    "target": self.target,
                    "duration": duration,
                    "result": self.result,
                },
            )
        return None
