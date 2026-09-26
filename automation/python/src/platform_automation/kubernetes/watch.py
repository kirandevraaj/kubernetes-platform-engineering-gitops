"""Watch-based readiness (event-driven with timeout)."""

from __future__ import annotations

import time
from typing import Any

from kubernetes import watch
from kubernetes.client.rest import ApiException

from platform_automation.errors import APIError, AutomationTimeoutError
from platform_automation.kubernetes.client import KubernetesFacade


def watch_deployment_ready(
    facade: KubernetesFacade,
    namespace: str,
    name: str,
    *,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Watch Deployment until Ready or timeout — not an infinite loop."""
    w = watch.Watch()
    started = time.monotonic()
    try:
        for event in w.stream(
            facade.apps.list_namespaced_deployment,
            namespace=namespace,
            field_selector=f"metadata.name={name}",
            timeout_seconds=int(timeout),
        ):
            obj = event["object"]
            desired = obj.spec.replicas or 0
            ready = obj.status.ready_replicas or 0
            if desired > 0 and ready >= desired:
                w.stop()
                return {
                    "name": name,
                    "namespace": namespace,
                    "status": "READY",
                    "event": event["type"],
                    "elapsed": time.monotonic() - started,
                }
            if time.monotonic() - started >= timeout:
                w.stop()
                break
    except ApiException as exc:
        raise APIError(f"watch failed: {exc.reason}", status_code=exc.status) from exc
    finally:
        w.stop()
    raise AutomationTimeoutError(f"watch: deployment {namespace}/{name} not ready within {timeout}s")
