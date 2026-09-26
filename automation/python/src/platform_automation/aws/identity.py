"""AWS identity (STS) helpers — read-only."""

from __future__ import annotations

from typing import Any

from platform_automation.errors import AuthenticationError


def get_caller_identity(sts_client: Any) -> dict[str, Any]:
    try:
        resp = sts_client.get_caller_identity()
    except Exception as exc:  # noqa: BLE001
        raise AuthenticationError(f"STS get_caller_identity failed: {exc}") from exc
    return {
        "Account": resp.get("Account"),
        "Arn": resp.get("Arn"),
        "UserId": resp.get("UserId"),
    }
