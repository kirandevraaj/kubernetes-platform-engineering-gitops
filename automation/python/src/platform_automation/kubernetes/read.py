"""Read helpers for common Kubernetes resources (no mutations)."""

from __future__ import annotations

from typing import Any

from kubernetes.client.rest import ApiException

from platform_automation.errors import APIError
from platform_automation.kubernetes.client import KubernetesFacade


def _not_found(exc: ApiException) -> bool:
    return exc.status == 404


def read_deployment(facade: KubernetesFacade, namespace: str, name: str) -> dict[str, Any]:
    try:
        dep = facade.apps.read_namespaced_deployment(name, namespace)
    except ApiException as exc:
        raise APIError(f"read deployment failed: {exc.reason}", status_code=exc.status) from exc
    return {
        "api_version": dep.api_version or "apps/v1",
        "kind": "Deployment",
        "name": dep.metadata.name,
        "namespace": dep.metadata.namespace,
        "replicas": dep.spec.replicas,
        "ready_replicas": getattr(dep.status, "ready_replicas", None),
        "labels": dep.metadata.labels or {},
    }


def read_service(facade: KubernetesFacade, namespace: str, name: str) -> dict[str, Any]:
    try:
        svc = facade.core.read_namespaced_service(name, namespace)
    except ApiException as exc:
        raise APIError(f"read service failed: {exc.reason}", status_code=exc.status) from exc
    return {
        "kind": "Service",
        "name": svc.metadata.name,
        "namespace": svc.metadata.namespace,
        "type": svc.spec.type,
        "cluster_ip": svc.spec.cluster_ip,
        "ports": [
            {"port": p.port, "target_port": str(p.target_port), "protocol": p.protocol}
            for p in (svc.spec.ports or [])
        ],
    }


def read_configmap(facade: KubernetesFacade, namespace: str, name: str) -> dict[str, Any]:
    try:
        cm = facade.core.read_namespaced_config_map(name, namespace)
    except ApiException as exc:
        raise APIError(f"read configmap failed: {exc.reason}", status_code=exc.status) from exc
    return {
        "kind": "ConfigMap",
        "name": cm.metadata.name,
        "namespace": cm.metadata.namespace,
        "data_keys": sorted((cm.data or {}).keys()),
    }


def read_statefulset(facade: KubernetesFacade, namespace: str, name: str) -> dict[str, Any]:
    try:
        sts = facade.apps.read_namespaced_stateful_set(name, namespace)
    except ApiException as exc:
        raise APIError(f"read statefulset failed: {exc.reason}", status_code=exc.status) from exc
    return {
        "kind": "StatefulSet",
        "name": sts.metadata.name,
        "namespace": sts.metadata.namespace,
        "replicas": sts.spec.replicas,
        "ready_replicas": getattr(sts.status, "ready_replicas", None),
    }


def read_pvc(facade: KubernetesFacade, namespace: str, name: str) -> dict[str, Any]:
    try:
        pvc = facade.core.read_namespaced_persistent_volume_claim(name, namespace)
    except ApiException as exc:
        raise APIError(f"read pvc failed: {exc.reason}", status_code=exc.status) from exc
    return {
        "kind": "PersistentVolumeClaim",
        "name": pvc.metadata.name,
        "namespace": pvc.metadata.namespace,
        "phase": pvc.status.phase if pvc.status else None,
        "storage_class": pvc.spec.storage_class_name,
    }


def read_hpa(facade: KubernetesFacade, namespace: str, name: str) -> dict[str, Any]:
    try:
        hpa = facade.autoscaling.read_namespaced_horizontal_pod_autoscaler(name, namespace)
    except ApiException as exc:
        raise APIError(f"read hpa failed: {exc.reason}", status_code=exc.status) from exc
    return {
        "kind": "HorizontalPodAutoscaler",
        "name": hpa.metadata.name,
        "namespace": hpa.metadata.namespace,
        "min_replicas": hpa.spec.min_replicas,
        "max_replicas": hpa.spec.max_replicas,
        "current_replicas": getattr(hpa.status, "current_replicas", None),
    }


def resource_exists(facade: KubernetesFacade, kind: str, namespace: str, name: str) -> bool:
    readers = {
        "deployment": read_deployment,
        "service": read_service,
        "configmap": read_configmap,
        "statefulset": read_statefulset,
        "pvc": read_pvc,
        "hpa": read_hpa,
    }
    reader = readers.get(kind.lower())
    if reader is None:
        raise APIError(f"unsupported kind for read: {kind}")
    try:
        reader(facade, namespace, name)
        return True
    except APIError as exc:
        if exc.status_code == 404:
            return False
        raise
