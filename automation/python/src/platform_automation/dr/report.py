"""DR report generation (JSON + human-readable). Never include secrets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from platform_automation.dr.rpo_rto import LAB_TARGETS
from platform_automation.dr.scenario import list_scenarios


SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "credential",
    "access_key",
    "private_key",
    "kubeconfig",
    "authorization",
}


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if any(s in str(key).lower() for s in SENSITIVE_KEYS):
                out[key] = "[redacted]"
            else:
                out[key] = _scrub(item)
        return out
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


def build_dr_report(
    *,
    scenario: str,
    failure_time: str | None = None,
    recovery_time: str | None = None,
    rto: dict[str, Any] | None = None,
    rpo: dict[str, Any] | None = None,
    recovery_mechanism: str = "",
    verification: dict[str, Any] | None = None,
    result: str = "UNKNOWN",
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "title": "Disaster Recovery Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario": scenario,
        "failure_time": failure_time,
        "recovery_time": recovery_time,
        "rto": rto,
        "rpo": rpo,
        "data_point": (rpo or {}).get("label") if rpo else None,
        "recovery_mechanism": recovery_mechanism,
        "verification": verification,
        "result": result,
        "lab_targets": LAB_TARGETS,
        "known_scenarios": list_scenarios(),
        "extras": extras or {},
    }
    return _scrub(payload)


def format_dr_report_text(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload.get('title', 'DR Report')}",
        f"generated_at: {payload.get('generated_at')}",
        f"scenario: {payload.get('scenario')}",
        f"result: {payload.get('result')}",
        f"failure_time: {payload.get('failure_time')}",
        f"recovery_time: {payload.get('recovery_time')}",
        f"recovery_mechanism: {payload.get('recovery_mechanism')}",
        "",
        "## RTO",
        json.dumps(payload.get("rto"), indent=2, default=str),
        "",
        "## RPO",
        json.dumps(payload.get("rpo"), indent=2, default=str),
        "",
        "## Verification",
        json.dumps(payload.get("verification"), indent=2, default=str),
        "",
    ]
    return "\n".join(lines)
