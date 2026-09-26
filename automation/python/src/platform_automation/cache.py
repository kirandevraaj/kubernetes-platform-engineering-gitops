"""Short-lived discovery cache with TTL (never cache credentials)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    value: T
    expires_at: float


class TtlCache:

    def __init__(self, default_ttl: float = 30.0) -> None:
        self.default_ttl = default_ttl
        self._store: dict[str, _Entry[Any]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        if any(s in key.lower() for s in ("token", "password", "secret", "credential")):
            raise ValueError("refusing to cache security-sensitive keys")
        self._store[key] = _Entry(value=value, expires_at=time.monotonic() + (ttl or self.default_ttl))

    def clear(self) -> None:
        self._store.clear()


# Alias for callers/tests that use the TTLCache name
TTLCache = TtlCache
