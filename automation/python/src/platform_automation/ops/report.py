"""Ops report formatting."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from platform_automation.ops.redact import scrub_mapping


def build_ops_report(
    *,
    context: str,
    health: dict[str, Any] | None = None,
    triage: dict[str, Any] | None = None,
    notes: str = "",
) -> dict[str, Any]:
    return scrub_mapping(
        {
            "title": "Platform Ops Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "context": context,
            "health": health,
            "triage": triage,
            "notes": notes,
            "mode": "read-only",
        }
    )


def format_ops_report_text(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload.get('title', 'Ops Report')}",
        f"generated_at: {payload.get('generated_at')}",
        f"context: {payload.get('context')}",
        "",
        "## Health",
        json.dumps(payload.get("health"), indent=2, default=str),
        "",
        "## Triage",
        json.dumps(payload.get("triage"), indent=2, default=str),
        "",
        f"notes: {payload.get('notes')}",
        "",
    ]
    return "\n".join(lines)
