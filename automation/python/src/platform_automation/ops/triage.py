"""Triage suggestion helpers (read-only guidance)."""

from __future__ import annotations

from typing import Any


LAYER_HINTS: dict[str, list[str]] = {
    "application": [
        "Check Deployment/Pods readiness and recent Git commit",
        "Verify Service Endpoints/EndpointSlices",
        "Confirm Argo Application Synced/Healthy",
    ],
    "ingress": [
        "VMware: ingress-nginx + MetalLB VIP; AWS: Ingress/ALB target health",
        "Confirm backends are Ready before blaming the edge",
    ],
    "node": [
        "kubectl get nodes; look for NotReady / pressure",
        "Distinguish cordon/drain (planned) from unexpected failure",
    ],
    "storage": [
        "PVC/PV Bound? VolumeAttachment? AZ mismatch for EBS?",
        "Do not manually attach/detach EBS",
    ],
    "gitops": [
        "Argo sync status / ComparisonError / OutOfSync",
        "Git desired state is authoritative; avoid kubectl edit persistence",
    ],
    "observability": [
        "Prometheus targets, Grafana Pod, metrics-server for HPA",
        "Kube-system scrape failures are not application incidents (Observed guidance)",
    ],
    "security": [
        "kubectl auth can-i; ServiceAccount; NetworkPolicy enforcement differs by env",
        "Do not grant cluster-admin while diagnosing",
    ],
}


def suggest_triage(
    symptom: str,
    *,
    layer: str | None = None,
) -> dict[str, Any]:
    text = (symptom or "").lower()
    guessed = layer
    if not guessed:
        if any(k in text for k in ("503", "5xx", "http", "health")):
            guessed = "application"
        elif "ingress" in text or "alb" in text or "metallb" in text:
            guessed = "ingress"
        elif "pvc" in text or "ebs" in text or "volume" in text:
            guessed = "storage"
        elif "node" in text or "notready" in text:
            guessed = "node"
        elif "argo" in text or "outofsync" in text or "comparison" in text:
            guessed = "gitops"
        elif "rbac" in text or "forbidden" in text or "networkpolicy" in text:
            guessed = "security"
        elif "prometheus" in text or "grafana" in text or "hpa" in text:
            guessed = "observability"
        else:
            guessed = "application"

    return {
        "symptom": symptom,
        "suggested_layer": guessed,
        "first_actions": LAYER_HINTS.get(guessed, LAYER_HINTS["application"]),
        "principle": (
            "Observe and collect evidence before changing the system. "
            "Prefer the smallest safe remediation."
        ),
        "mode": "read-only-guidance",
    }
