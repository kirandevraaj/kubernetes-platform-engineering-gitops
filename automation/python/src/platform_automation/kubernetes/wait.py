"""Wait helpers with deadline — no infinite polling."""

from __future__ import annotations

import time
from typing import Any

from kubernetes.client.rest import ApiException

from platform_automation.errors import APIError, AutomationTimeoutError
from platform_automation.kubernetes.client import KubernetesFacade


def wait_for_deployment_ready(
    facade: KubernetesFacade,
    namespace: str,
    name: str,
    *,
    timeout: float = 120.0,
    poll_interval: float = 2.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        try:
            dep = facade.apps.read_namespaced_deployment(name, namespace)
        except ApiException as exc:
            raise APIError(f"wait deployment failed: {exc.reason}", status_code=exc.status) from exc
        desired = dep.spec.replicas or 0
        ready = dep.status.ready_replicas or 0
        available = dep.status.available_replicas or 0
        last = {
            "name": name,
            "namespace": namespace,
            "desired": desired,
            "ready": ready,
            "available": available,
            "status": "READY" if desired > 0 and ready >= desired and available >= desired else "WAITING",
        }
        if last["status"] == "READY":
            return last
        time.sleep(poll_interval)
    raise AutomationTimeoutError(f"deployment {namespace}/{name} not ready within {timeout}s: {last}")


def wait_for_pod_ready(
    facade: KubernetesFacade,
    namespace: str,
    name: str,
    *,
    timeout: float = 120.0,
    poll_interval: float = 2.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            pod = facade.core.read_namespaced_pod(name, namespace)
        except ApiException as exc:
            raise APIError(f"wait pod failed: {exc.reason}", status_code=exc.status) from exc
        ready = False
        if pod.status and pod.status.conditions:
            ready = any(c.type == "Ready" and c.status == "True" for c in pod.status.conditions)
        if ready:
            return {"name": name, "namespace": namespace, "status": "READY", "phase": pod.status.phase}
        time.sleep(poll_interval)
    raise AutomationTimeoutError(f"pod {namespace}/{name} not ready within {timeout}s")


def wait_for_job_complete(
    facade: KubernetesFacade,
    namespace: str,
    name: str,
    *,
    timeout: float = 180.0,
    poll_interval: float = 2.0,
) -> dict[str, Any]:
    from kubernetes.client import BatchV1Api

    batch = BatchV1Api(facade.api_client)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            job = batch.read_namespaced_job(name, namespace)
        except ApiException as exc:
            raise APIError(f"wait job failed: {exc.reason}", status_code=exc.status) from exc
        succeeded = job.status.succeeded or 0
        failed = job.status.failed or 0
        if succeeded > 0:
            return {"name": name, "namespace": namespace, "status": "COMPLETE", "succeeded": succeeded}
        if failed > 0:
            return {"name": name, "namespace": namespace, "status": "FAILED", "failed": failed}
        time.sleep(poll_interval)
    raise AutomationTimeoutError(f"job {namespace}/{name} not complete within {timeout}s")


def wait_for_deletion(
    facade: KubernetesFacade,
    kind: str,
    namespace: str,
    name: str,
    *,
    timeout: float = 60.0,
    poll_interval: float = 2.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if kind.lower() == "deployment":
                facade.apps.read_namespaced_deployment(name, namespace)
            elif kind.lower() == "pod":
                facade.core.read_namespaced_pod(name, namespace)
            elif kind.lower() == "namespace":
                facade.core.read_namespace(name)
            else:
                raise APIError(f"unsupported kind for deletion wait: {kind}")
        except ApiException as exc:
            if exc.status == 404:
                return {"name": name, "namespace": namespace, "kind": kind, "status": "DELETED"}
            raise APIError(f"wait deletion failed: {exc.reason}", status_code=exc.status) from exc
        time.sleep(poll_interval)
    raise AutomationTimeoutError(f"{kind} {namespace}/{name} not deleted within {timeout}s")
