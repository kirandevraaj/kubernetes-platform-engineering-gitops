"""Tiny local test helpers / mock API for unit tests."""

from __future__ import annotations

from typing import Any


class LocalMockTransport:
    """Minimal in-memory handler for ApiClient tests without network."""

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], dict[str, Any]] = {}
        self.calls: list[tuple[str, str]] = []

    def add(
        self,
        method: str,
        path: str,
        *,
        status_code: int = 200,
        json_body: Any | None = None,
        text: str = "",
    ) -> None:
        self.routes[(method.upper(), path)] = {
            "status_code": status_code,
            "json": json_body,
            "text": text,
        }

    def handle(self, method: str, url: str) -> dict[str, Any]:
        # Match by path suffix
        from urllib.parse import urlparse

        path = urlparse(url).path
        self.calls.append((method.upper(), path))
        key = (method.upper(), path)
        if key not in self.routes:
            return {"status_code": 404, "json": {"error": "not found"}, "text": "not found"}
        return self.routes[key]


def health_payload() -> dict[str, Any]:
    return {"status": "ok", "service": "automation-lab-local-api"}
