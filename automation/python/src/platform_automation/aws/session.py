"""AWS session helpers — never embed credentials."""

from __future__ import annotations

from typing import Any

import boto3
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
)

from platform_automation.errors import APIError, AuthenticationError


def build_session(*, profile: str | None = None, region: str | None = None) -> boto3.Session:
    try:
        kwargs: dict[str, Any] = {}
        if profile:
            kwargs["profile_name"] = profile
        if region:
            kwargs["region_name"] = region
        return boto3.Session(**kwargs)
    except BotoCoreError as exc:
        raise AuthenticationError(f"failed to create boto3 session: {exc}") from exc


def client_for(session: boto3.Session, service: str):
    return session.client(service)


def translate_client_error(exc: ClientError) -> APIError:
    code = exc.response.get("Error", {}).get("Code", "Unknown")
    message = exc.response.get("Error", {}).get("Message", str(exc))
    retryable = code in {
        "Throttling",
        "ThrottlingException",
        "RequestLimitExceeded",
        "TooManyRequestsException",
        "ServiceUnavailable",
        "RequestTimeout",
        "PriorRequestNotComplete",
    }
    if code in {"UnauthorizedOperation", "AccessDenied", "AccessDeniedException", "AuthFailure"}:
        return AuthenticationError(f"AWS authorization failure ({code}): {message}")  # type: ignore[return-value]
    if code in {"InvalidClientTokenId", "ExpiredToken", "UnrecognizedClientException"}:
        return AuthenticationError(f"AWS authentication failure ({code}): {message}")  # type: ignore[return-value]
    not_found = code.endswith(".NotFound") or code in {
        "ResourceNotFoundException",
        "NoSuchEntity",
        "InvalidInstanceID.NotFound",
    }
    return APIError(
        f"AWS ClientError ({code}): {message}",
        status_code=404 if not_found else None,
        retryable=retryable,
    )


def safe_call(fn):
    try:
        return fn()
    except NoCredentialsError as exc:
        raise AuthenticationError("AWS credentials not found") from exc
    except EndpointConnectionError as exc:
        raise APIError(f"AWS endpoint connection error: {exc}", retryable=True) from exc
    except ClientError as exc:
        mapped = translate_client_error(exc)
        raise mapped from exc
