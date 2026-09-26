"""Read-only ops health aggregation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from platform_automation.ops.redact import scrub_mapping


def _status(ok: bool | None) -> str:
    if ok is True:
        return "PASS"
    if ok is False:
        return "FAIL"
    return "UNKNOWN"


def collect_ops_health(
    *,
    kubernetes_api_ok: bool | None = None,
    nodes_ready: bool | None = None,
    argo_synced: bool | None = None,
    applications_healthy: bool | None = None,
    pvc_bound: bool | None = None,
    observability_ok: bool | None = None,
    application_ready: bool | None = None,
    extras: dict[str, bool | None] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate operator-provided boolean signals.

    Network I/O is intentionally left to the CLI so unit tests stay hermetic and
    evidence collection can fail closed without printing secrets.
    """
    checks = [
        {"name": "kubernetes_api", "result": _status(kubernetes_api_ok)},
        {"name": "nodes_ready", "result": _status(nodes_ready)},
        {"name": "argo_synced", "result": _status(argo_synced)},
        {"name": "applications_healthy", "result": _status(applications_healthy)},
        {"name": "pvc_bound", "result": _status(pvc_bound)},
        {"name": "observability", "result": _status(observability_ok)},
        {"name": "application_ready", "result": _status(application_ready)},
    ]
    for key, value in (extras or {}).items():
        checks.append({"name": key, "result": _status(value)})

    results = [c["result"] for c in checks]
    if "FAIL" in results:
        overall = "FAIL"
    elif all(r == "PASS" for r in results):
        overall = "PASS"
    else:
        overall = "UNKNOWN"

    return scrub_mapping(
        {
            "title": "Platform Ops Health",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall": overall,
            "checks": checks,
            "details": details or {},
            "mode": "read-only",
        }
    )
