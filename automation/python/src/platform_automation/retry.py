"""Retry with exponential backoff and jitter for transient failures only."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

from platform_automation.errors import APIError, AutomationTimeoutError

T = TypeVar("T")


def is_transient(exc: BaseException) -> bool:
    if isinstance(exc, APIError):
        return exc.retryable
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    name = type(exc).__name__
    return name in {
        "EndpointConnectionError",
        "ConnectionClosedError",
        "ReadTimeoutError",
        "ConnectTimeoutError",
        "Throttling",
        "RequestLimitExceeded",
        "TooManyRequestsException",
        "ServiceUnavailable",
        "ApiException",  # only when caller wraps as retryable APIError preferred
    }


def retry(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 0.2,
    max_delay: float = 5.0,
    jitter: float = 0.2,
    deadline: float | None = None,
    should_retry: Callable[[BaseException], bool] = is_transient,
) -> T:
    """Execute ``fn`` with exponential backoff.

    Does **not** retry permanent errors (auth, validation, not-found).
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")
    start = time.monotonic()
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — re-raised after policy
            if attempt >= max_attempts or not should_retry(exc):
                raise
            if deadline is not None and time.monotonic() - start >= deadline:
                raise AutomationTimeoutError(
                    f"retry deadline exceeded after {attempt} attempts"
                ) from exc
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            delay += random.uniform(0, jitter)
            if deadline is not None:
                remaining = deadline - (time.monotonic() - start)
                if remaining <= 0:
                    raise AutomationTimeoutError("retry deadline exceeded") from exc
                delay = min(delay, remaining)
            time.sleep(delay)
