"""Kubernetes client loading and context selection."""

from __future__ import annotations

from typing import Any

from kubernetes import client, config
from kubernetes.client import ApiClient, AppsV1Api, AutoscalingV1Api, CoreV1Api
from kubernetes.config.config_exception import ConfigException

from platform_automation.errors import AuthenticationError, ConfigurationError


def load_api_client(context: str | None = None) -> ApiClient:
    try:
        if context:
            config.load_kube_config(context=context)
        else:
            config.load_kube_config()
    except ConfigException as exc:
        raise AuthenticationError(f"failed to load kubeconfig: {exc}") from exc
    return client.ApiClient()


def get_current_context() -> str:
    try:
        _contexts, active = config.list_kube_config_contexts()
    except ConfigException as exc:
        raise AuthenticationError(f"failed to list kube contexts: {exc}") from exc
    if active and active.get("name"):
        return str(active["name"])
    raise ConfigurationError("no active kube context")


def list_context_names() -> list[str]:
    try:
        contexts, _active = config.list_kube_config_contexts()
    except ConfigException as exc:
        raise AuthenticationError(f"failed to list kube contexts: {exc}") from exc
    return [str(c["name"]) for c in contexts]


class KubernetesFacade:
    """Thin facade over official client APIs (injected into controller)."""

    def __init__(self, api_client: ApiClient | None = None, context: str | None = None) -> None:
        self.api_client = api_client or load_api_client(context)
        self.core = CoreV1Api(self.api_client)
        self.apps = AppsV1Api(self.api_client)
        self.autoscaling = AutoscalingV1Api(self.api_client)

    def list_nodes(self) -> list[dict[str, Any]]:
        nodes = self.core.list_node().items
        out: list[dict[str, Any]] = []
        for node in nodes:
            status = "Unknown"
            for cond in node.status.conditions or []:
                if cond.type == "Ready":
                    status = "Ready" if cond.status == "True" else "NotReady"
            labels = node.metadata.labels or {}
            capacity = node.status.capacity or {}
            node_info = node.status.node_info
            out.append(
                {
                    "name": node.metadata.name,
                    "status": status,
                    "cpu": capacity.get("cpu"),
                    "memory": capacity.get("memory"),
                    "version": node_info.kubelet_version if node_info else None,
                    "az": labels.get("topology.kubernetes.io/zone")
                    or labels.get("failure-domain.beta.kubernetes.io/zone"),
                }
            )
        return out

    def list_namespaces(self) -> list[str]:
        return [ns.metadata.name for ns in self.core.list_namespace().items]

    def list_pods(self, namespace: str) -> list[dict[str, Any]]:
        pods = self.core.list_namespaced_pod(namespace).items
        return [
            {
                "name": p.metadata.name,
                "namespace": p.metadata.namespace,
                "phase": p.status.phase,
                "ready": _pod_ready(p),
                "node": p.spec.node_name,
            }
            for p in pods
        ]


def _pod_ready(pod: Any) -> bool:
    if not pod.status or not pod.status.conditions:
        return False
    return any(c.type == "Ready" and c.status == "True" for c in pod.status.conditions)
