"""RPO/RTO calculation helpers. Do not hardcode lab timestamps."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from platform_automation.dr.timeline import parse_time


@dataclass
class RpoResult:
    """Data-loss window relative to a recovery point."""

    recovery_point: datetime
    failure_or_change: datetime
    loss_window_seconds: float
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_point": self.recovery_point.isoformat(),
            "failure_or_change": self.failure_or_change.isoformat(),
            "loss_window_seconds": self.loss_window_seconds,
            "loss_window_minutes": round(self.loss_window_seconds / 60.0, 3),
            "label": self.label,
            "note": (
                "RPO demonstrated by this experiment is the elapsed time between "
                "the recovery point and the post-snapshot change — not a production SLO."
            ),
        }


@dataclass
class RtoResult:
    """Service-recovery duration between two timeline marks."""

    start: datetime
    end: datetime
    recovery_seconds: float
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "recovery_seconds": self.recovery_seconds,
            "recovery_minutes": round(self.recovery_seconds / 60.0, 3),
            "label": self.label,
            "note": "Observed lab RTO for this drill — not a production commitment.",
        }


def compute_rpo(
    recovery_point: str | datetime,
    failure_or_change: str | datetime,
    *,
    label: str = "",
) -> RpoResult:
    rp = parse_time(recovery_point)
    fc = parse_time(failure_or_change)
    return RpoResult(
        recovery_point=rp,
        failure_or_change=fc,
        loss_window_seconds=(fc - rp).total_seconds(),
        label=label,
    )


def compute_rto(
    start: str | datetime,
    end: str | datetime,
    *,
    label: str = "",
) -> RtoResult:
    s = parse_time(start)
    e = parse_time(end)
    return RtoResult(
        start=s,
        end=e,
        recovery_seconds=(e - s).total_seconds(),
        label=label,
    )


# Lab targets (objectives, not production SLOs)
LAB_TARGETS: dict[str, Any] = {
    "configuration_rpo": "0 committed changes (Git is source of truth)",
    "application_recovery_rto_target_minutes": 10,
    "ebs_snapshot_recovery_rto": "measure actual",
    "node_failure_rto_prior_minutes": 6.3,
    "namespace_argo_recovery_rto": "measure actual",
    "infrastructure_rebuild": "documented / plan duration only if safely tested",
}
