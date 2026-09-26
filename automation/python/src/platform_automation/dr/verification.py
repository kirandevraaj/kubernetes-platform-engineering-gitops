"""Read-only DR verification checks. Returns PASS / FAIL / UNKNOWN."""

from __future__ import annotations

from typing import Any


def check_result(name: str, ok: bool | None, detail: str = "") -> dict[str, Any]:
    if ok is True:
        result = "PASS"
    elif ok is False:
        result = "FAIL"
    else:
        result = "UNKNOWN"
    return {"name": name, "result": result, "detail": detail}


def verify_platform(
    *,
    kubernetes_api_ok: bool | None = None,
    nodes_ready: bool | None = None,
    argo_healthy: bool | None = None,
    applications_synced: bool | None = None,
    pvc_bound: bool | None = None,
    ebs_attached: bool | None = None,
    observability_ok: bool | None = None,
    application_healthy: bool | None = None,
    extras: dict[str, bool | None] | None = None,
) -> dict[str, Any]:
    """Aggregate boolean signals gathered by the caller (CLI/runbook).

    This function itself performs no network I/O so unit tests stay hermetic.
    """
    checks = [
        check_result("kubernetes_api", kubernetes_api_ok),
        check_result("nodes_ready", nodes_ready),
        check_result("argo_healthy", argo_healthy),
        check_result("applications_synced", applications_synced),
        check_result("pvc_bound", pvc_bound),
        check_result("ebs_attached", ebs_attached),
        check_result("observability", observability_ok),
        check_result("application_health", application_healthy),
    ]
    for key, value in (extras or {}).items():
        checks.append(check_result(key, value))

    results = [c["result"] for c in checks]
    if "FAIL" in results:
        overall = "FAIL"
    elif all(r == "PASS" for r in results):
        overall = "PASS"
    else:
        overall = "UNKNOWN"

    return {"overall": overall, "checks": checks}
