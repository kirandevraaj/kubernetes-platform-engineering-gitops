"""Live Kubernetes collectors for ops health/evidence (read-only)."""

from __future__ import annotations

from typing import Any

from platform_automation.kubernetes.client import KubernetesFacade
from platform_automation.ops.health import collect_ops_health
from platform_automation.ops.redact import scrub_mapping


def _nodes_ready(facade: KubernetesFacade) -> tuple[bool | None, str]:
    try:
        nodes = facade.list_nodes()
        if not nodes:
            return False, "no nodes"
        not_ready = [n["name"] for n in nodes if n.get("status") != "Ready"]
        if not_ready:
            return False, f"not Ready: {', '.join(not_ready)}"
        return True, f"{len(nodes)} Ready"
    except Exception as exc:  # noqa: BLE001
        return None, f"{exc.__class__.__name__}"


def _deployment_ready(facade: KubernetesFacade, namespace: str, name: str) -> tuple[bool | None, str]:
    try:
        from platform_automation.kubernetes.read import read_deployment

        dep = read_deployment(facade, namespace, name)
        ready = dep.get("ready_replicas") or 0
        desired = dep.get("replicas") or 0
        ok = desired > 0 and ready >= desired
        return ok, f"{ready}/{desired}"
    except Exception as exc:  # noqa: BLE001
        return None, exc.__class__.__name__


def _pvc_bound(facade: KubernetesFacade, namespace: str, name: str) -> tuple[bool | None, str]:
    try:
        from platform_automation.kubernetes.read import read_pvc

        pvc = read_pvc(facade, namespace, name)
        phase = pvc.get("phase")
        return phase == "Bound", str(phase)
    except Exception as exc:  # noqa: BLE001
        return None, exc.__class__.__name__


def _argo_summary(facade: KubernetesFacade) -> tuple[bool | None, bool | None, str]:
    """Best-effort Argo Application list via dynamic client if available."""
    try:
        from kubernetes import dynamic

        client = dynamic.DynamicClient(facade.api_client)
        api = client.resources.get(api_version="argoproj.io/v1alpha1", kind="Application")
        apps = api.get(namespace="argocd")
        items = getattr(apps, "items", None) or []
        if not items:
            return None, None, "no Applications in argocd"
        sync_ok = True
        bits = []
        for app in items:
            name = app.metadata.name
            sync = (app.status.sync.status if app.status and app.status.sync else None) or "Unknown"
            health = (
                app.status.health.status if app.status and app.status.health else None
            ) or "Unknown"
            bits.append(f"{name}:{sync}/{health}")
            if sync != "Synced":
                sync_ok = False
        healthyish = all(
            b.endswith("/Healthy") or b.endswith("/Progressing") for b in bits
        ) if bits else False
        return sync_ok, healthyish, "; ".join(bits[:12])
    except Exception as exc:  # noqa: BLE001
        return None, None, exc.__class__.__name__


def live_ops_health(facade: KubernetesFacade, *, environment: str) -> dict[str, Any]:
    api_ok = True
    nodes_ok, nodes_detail = _nodes_ready(facade)
    app_ok, app_detail = _deployment_ready(facade, "platform-lab", "platform-lab")
    storage_ns = "storage-lab"
    pvc_ok, pvc_detail = _pvc_bound(facade, storage_ns, "data-storage-demo-0")
    argo_sync, argo_health, argo_detail = _argo_summary(facade)

    obs_ns = "monitoring" if environment == "vmware" else "observability"
    obs_ok, obs_detail = _deployment_ready(
        facade, obs_ns, "grafana" if environment == "aws" else "kube-prometheus-stack-grafana"
    )
    # VMware grafana deploy name may differ — soft UNKNOWN on failure
    if obs_ok is None and environment == "vmware":
        obs_ok, obs_detail = _deployment_ready(facade, "monitoring", "kube-prometheus-stack-operator")

    return collect_ops_health(
        kubernetes_api_ok=api_ok,
        nodes_ready=nodes_ok,
        argo_synced=argo_sync,
        applications_healthy=argo_health,
        pvc_bound=pvc_ok,
        observability_ok=obs_ok,
        application_ready=app_ok,
        details=scrub_mapping(
            {
                "nodes": nodes_detail,
                "platform_lab": app_detail,
                "storage_pvc": pvc_detail,
                "argo": argo_detail,
                "observability": obs_detail,
                "environment": environment,
            }
        ),
    )


def live_evidence_collectors(facade: KubernetesFacade) -> dict[str, Any]:
    def nodes() -> str:
        return "\n".join(
            f"{n.get('name')} {n.get('status')}" for n in facade.list_nodes()
        ) or "none"

    def namespaces() -> str:
        return "\n".join(facade.list_namespaces())

    def pods_platform() -> str:
        return "\n".join(
            f"{p.get('name')} {p.get('phase')}" for p in facade.list_pods("platform-lab")
        )

    def applications() -> str:
        sync_ok, healthyish, detail = _argo_summary(facade)
        return f"sync_ok={sync_ok} healthyish={healthyish}\n{detail}"

    def storage() -> str:
        try:
            from platform_automation.kubernetes.read import read_pvc

            pvc = read_pvc(facade, "storage-lab", "data-storage-demo-0")
            return f"data-storage-demo-0 phase={pvc.get('phase')}"
        except Exception as exc:  # noqa: BLE001
            return f"storage_read_error={exc.__class__.__name__}"

    def application_health() -> str:
        ok, detail = _deployment_ready(facade, "platform-lab", "platform-lab")
        return f"platform-lab ready={ok} detail={detail}"

    return {
        "nodes": nodes,
        "namespaces": namespaces,
        "applications": applications,
        "pods-platform-lab": pods_platform,
        "storage": storage,
        "application-health": application_health,
    }
