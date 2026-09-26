"""REST API client — transport separated from domain logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from platform_automation.errors import APIError, AuthenticationError
from platform_automation.retry import retry


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    headers: dict[str, str] = field(default_factory=dict)
    json_body: Any | None = None
    params: dict[str, Any] | None = None


@dataclass(frozen=True)
class Response:
    status_code: int
    headers: dict[str, str]
    json_body: Any | None
    text: str
    request_id: str | None = None


class ApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
        max_retries: int = 3,
        transport: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = headers or {"Accept": "application/json"}
        self.max_retries = max_retries
        self._client = transport or httpx.Client(base_url=self.base_url, timeout=timeout)
        self._owns_client = transport is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def send(self, request: Request) -> Response:
        def _do() -> Response:
            try:
                resp = self._client.request(
                    request.method.upper(),
                    request.path,
                    headers={**self.default_headers, **request.headers},
                    json=request.json_body,
                    params=request.params,
                )
            except httpx.TimeoutException as exc:
                raise APIError(f"HTTP timeout: {exc}", retryable=True) from exc
            except httpx.TransportError as exc:
                raise APIError(f"HTTP transport error: {exc}", retryable=True) from exc

            request_id = resp.headers.get("x-request-id") or resp.headers.get("X-Request-Id")
            body: Any | None
            try:
                body = resp.json()
            except ValueError:
                body = None
            if resp.status_code in {401, 403}:
                raise AuthenticationError(f"HTTP {resp.status_code} auth failure")
            if resp.status_code in {429, 502, 503, 504}:
                raise APIError(
                    f"HTTP {resp.status_code} retryable",
                    status_code=resp.status_code,
                    retryable=True,
                )
            if resp.status_code >= 400:
                raise APIError(
                    f"HTTP {resp.status_code}: {resp.text[:200]}",
                    status_code=resp.status_code,
                    retryable=False,
                )
            return Response(
                status_code=resp.status_code,
                headers=dict(resp.headers),
                json_body=body,
                text=resp.text,
                request_id=request_id,
            )

        return retry(_do, max_attempts=self.max_retries)

    def get(self, path: str, **kwargs: Any) -> Response:
        return self.send(Request("GET", path, **kwargs))

    def post(self, path: str, **kwargs: Any) -> Response:
        return self.send(Request("POST", path, **kwargs))

    def put(self, path: str, **kwargs: Any) -> Response:
        return self.send(Request("PUT", path, **kwargs))

    def patch(self, path: str, **kwargs: Any) -> Response:
        return self.send(Request("PATCH", path, **kwargs))

    def delete(self, path: str, **kwargs: Any) -> Response:
        return self.send(Request("DELETE", path, **kwargs))
