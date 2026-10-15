"""Human-readable and JSON report helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from platform_automation.errors import ValidationError

DEFAULT_REPORT_DIR = "automation/reports"


def build_report(
    title: str,
    sections: dict[str, Any],
    *,
    status: str = "ok",
) -> dict[str, Any]:
    return {
        "title": title,
        "status": status,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": sections,
    }


def write_report(
    name: str,
    payload: dict[str, Any],
    *,
    report_dir: Path | str | None = None,
) -> Path:
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValidationError(f"invalid report name: {name!r}")
    path = Path(report_dir or DEFAULT_REPORT_DIR)
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"{name}.json"
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return out


def format_text_report(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload.get('title', 'report')}",
        f"status: {payload.get('status')}",
        f"generated_at: {payload.get('generated_at')}",
        "",
    ]
    for key, value in (payload.get("sections") or {}).items():
        lines.append(f"## {key}")
        if isinstance(value, (dict, list)):
            lines.append(json.dumps(value, indent=2, default=str))
        else:
            lines.append(str(value))
        lines.append("")
    return "\n".join(lines)
