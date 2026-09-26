"""Unit tests for DR helpers."""

from __future__ import annotations

from platform_automation.dr import (
    Timeline,
    build_dr_report,
    compute_rpo,
    compute_rto,
    list_scenarios,
    verify_platform,
)


def test_list_scenarios_nonempty():
    scenarios = list_scenarios()
    assert len(scenarios) >= 5
    assert all("name" in s for s in scenarios)


def test_timeline_duration():
    tl = Timeline()
    tl.mark("t0", "2026-09-26T10:00:00+00:00")
    tl.mark("t1", "2026-09-26T10:05:30+00:00")
    assert tl.duration_seconds("t0", "t1") == 330.0


def test_rpo_rto():
    rpo = compute_rpo("2026-09-26T10:00:00Z", "2026-09-26T10:20:00Z", label="example")
    assert rpo.loss_window_seconds == 1200.0
    rto = compute_rto("2026-09-26T10:00:00Z", "2026-09-26T10:08:00Z", label="example")
    assert rto.recovery_seconds == 480.0


def test_verify_and_report_scrub():
    v = verify_platform(kubernetes_api_ok=True, nodes_ready=True, argo_healthy=None)
    assert v["overall"] == "UNKNOWN"
    report = build_dr_report(
        scenario="namespace_deleted",
        result="PASS",
        extras={"token": "should-not-leak", "ok": True},
    )
    assert report["extras"]["token"] == "[redacted]"
    assert report["extras"]["ok"] is True
