"""AWS-specific error helpers."""

from __future__ import annotations

from platform_automation.errors import APIError, AuthenticationError


def translate_botocore_error(exc: BaseException) -> Exception:
    """Map common botocore errors to package exceptions."""
    code = getattr(exc, "response", {}).get("Error", {}).get("Code") if hasattr(exc, "response") else None
    message = str(exc)
    if code in {"UnrecognizedClientException", "InvalidClientTokenId", "ExpiredToken"}:
        return AuthenticationError(message)
    return APIError(message, details={"code": code})
