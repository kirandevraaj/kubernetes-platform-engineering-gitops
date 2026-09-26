"""Unit tests for ops helpers."""

from __future__ import annotations

from pathlib import Path

from platform_automation.ops import (
    build_ops_report,
    collect_evidence_bundle,
    collect_ops_health,
    redact_text,
    suggest_triage,
)


def test_ops_health_unknown_default():
    payload = collect_ops_health()
    assert payload["overall"] == "UNKNOWN"
    assert payload["mode"] == "read-only"


def test_ops_health_fail():
    payload = collect_ops_health(nodes_ready=False, kubernetes_api_ok=True)
    assert payload["overall"] == "FAIL"


def test_triage_guesses_storage():
    result = suggest_triage("PVC Pending and EBS attach")
    assert result["suggested_layer"] == "storage"


def test_redact_and_evidence(tmp_path: Path):
    assert "[redacted]" in redact_text("password: hunter2")
    bundle = collect_evidence_bundle(
        output_dir=tmp_path,
        context="ckad-lab",
        collectors={
            "nodes": lambda: "k8s-worker-01 Ready",
            "secret-dump": lambda: "should never run",
        },
    )
    assert "nodes.txt" in bundle["manifest"]["files"]
    assert any("rejected" in e.get("error", "") for e in bundle["manifest"]["errors"])
    report = build_ops_report(context="ckad-lab", health=collect_ops_health(kubernetes_api_ok=True))
    assert report["context"] == "ckad-lab"
