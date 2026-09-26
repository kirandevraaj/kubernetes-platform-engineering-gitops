"""Disaster recovery automation package (Section 25)."""

from platform_automation.dr.report import build_dr_report, format_dr_report_text
from platform_automation.dr.rpo_rto import LAB_TARGETS, compute_rpo, compute_rto
from platform_automation.dr.scenario import get_scenario, list_scenarios
from platform_automation.dr.timeline import Timeline
from platform_automation.dr.verification import verify_platform

__all__ = [
    "LAB_TARGETS",
    "Timeline",
    "build_dr_report",
    "compute_rpo",
    "compute_rto",
    "format_dr_report_text",
    "get_scenario",
    "list_scenarios",
    "verify_platform",
]
