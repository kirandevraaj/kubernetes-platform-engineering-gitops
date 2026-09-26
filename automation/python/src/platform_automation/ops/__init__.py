"""Read-only platform operations helpers (Section 26)."""

from platform_automation.ops.evidence import collect_evidence_bundle
from platform_automation.ops.health import collect_ops_health
from platform_automation.ops.redact import redact_text
from platform_automation.ops.report import build_ops_report, format_ops_report_text
from platform_automation.ops.triage import suggest_triage

__all__ = [
    "build_ops_report",
    "collect_evidence_bundle",
    "collect_ops_health",
    "format_ops_report_text",
    "redact_text",
    "suggest_triage",
]
