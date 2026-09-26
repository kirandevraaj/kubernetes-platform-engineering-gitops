"""Idempotent create/update/delete for automation-lab demo resources only."""

from __future__ import annotations

from typing import Any

from kubernetes import client
from kubernetes.client.rest import ApiException

from platform_automation.errors import APIError, ValidationError
from platform_automation.kubernetes.client import KubernetesFacade
from platform_automation.validation import require_namespace, require_resource_name

LAB_NS = "automation-lab"
DEMO = "automation-demo"
DEMO_CM = "automation-demo-config"


def _ensure_namespace(facade: KubernetesFacade, dry_run: bool = False) -> str:
    require_namespace(LAB_NS, mutation=True)
    try:
        facade.core.read_namespace(LAB_NS)
        return "exists"
    except ApiException as exc:
        if exc.status != 404:
            raise APIError(f"read namespace failed: {exc.reason}", status_code=exc.status) from exc
    if dry_run:
        return "would-create"
    body = client.V1Namespace(metadata=client.V1ObjectMeta(name=LAB_NS, labels={"app": "automation-lab"}))
    facade.core.create_namespace(body)
    return "created"


def desired_configmap_data(message: str = "hello-automation") -> dict[str, str]:
    return {"message": message, "managed_by": "platform-automation"}


def ensure_demo_configmap(
    facade: KubernetesFacade,
    *,
    message: str = "hello-automation",
    dry_run: bool = False,
) -> dict[str, Any]:
    require_resource_name(DEMO_CM, mutation=True)
    ns_state = _ensure_namespace(facade, dry_run=dry_run)
    desired = desired_configmap_data(message)
    try:
        current = facade.core.read_namespaced_config_map(DEMO_CM, LAB_NS)
        if (current.data or {}) == desired:
            return {"resource": "ConfigMap", "name": DEMO_CM, "action": "unchanged", "namespace": LAB_NS, "ns": ns_state}
        if dry_run:
            return {"resource": "ConfigMap", "name": DEMO_CM, "action": "would-update", "namespace": LAB_NS}
        current.data = desired
        facade.core.patch_namespaced_config_map(DEMO_CM, LAB_NS, current)
        return {"resource": "ConfigMap", "name": DEMO_CM, "action": "updated", "namespace": LAB_NS}
    except ApiException as exc:
        if exc.status != 404:
            raise APIError(f"configmap ensure failed: {exc.reason}", status_code=exc.status) from exc
    if dry_run:
        return {"resource": "ConfigMap", "name": DEMO_CM, "action": "would-create", "namespace": LAB_NS}
    body = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(name=DEMO_CM, namespace=LAB_NS, labels={"app": DEMO}),
        data=desired,
    )
    facade.core.create_namespaced_config_map(LAB_NS, body)
    return {"resource": "ConfigMap", "name": DEMO_CM, "action": "created", "namespace": LAB_NS}


def ensure_demo_deployment(
    facade: KubernetesFacade,
    *,
    replicas: int = 1,
    image: str = "public.ecr.aws/nginx/nginx:1.27",
    dry_run: bool = False,
) -> dict[str, Any]:
    require_resource_name(DEMO, mutation=True)
    _ensure_namespace(facade, dry_run=dry_run)
    labels = {"app": DEMO}
    try:
        current = facade.apps.read_namespaced_deployment(DEMO, LAB_NS)
        changed = False
        if current.spec.replicas != replicas:
            current.spec.replicas = replicas
            changed = True
        container = current.spec.template.spec.containers[0]
        if container.image != image:
            container.image = image
            changed = True
        if not changed:
            return {"resource": "Deployment", "name": DEMO, "action": "unchanged", "namespace": LAB_NS}
        if dry_run:
            return {"resource": "Deployment", "name": DEMO, "action": "would-update", "namespace": LAB_NS}
        # Patch selected fields — prefer patch over full replace for safety
        facade.apps.patch_namespaced_deployment(DEMO, LAB_NS, current)
        return {"resource": "Deployment", "name": DEMO, "action": "updated", "namespace": LAB_NS}
    except ApiException as exc:
        if exc.status != 404:
            raise APIError(f"deployment ensure failed: {exc.reason}", status_code=exc.status) from exc
    if dry_run:
        return {"resource": "Deployment", "name": DEMO, "action": "would-create", "namespace": LAB_NS}
    body = client.V1Deployment(
        metadata=client.V1ObjectMeta(name=DEMO, namespace=LAB_NS, labels=labels),
        spec=client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels=labels),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels=labels),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name=DEMO,
                            image=image,
                            ports=[client.V1ContainerPort(container_port=80)],
                        )
                    ]
                ),
            ),
        ),
    )
    facade.apps.create_namespaced_deployment(LAB_NS, body)
    return {"resource": "Deployment", "name": DEMO, "action": "created", "namespace": LAB_NS}


def ensure_demo_service(facade: KubernetesFacade, *, dry_run: bool = False) -> dict[str, Any]:
    require_resource_name(DEMO, mutation=True)
    _ensure_namespace(facade, dry_run=dry_run)
    labels = {"app": DEMO}
    try:
        current = facade.core.read_namespaced_service(DEMO, LAB_NS)
        # Service clusterIP is immutable — only compare ports/selector
        ports = current.spec.ports or []
        if ports and ports[0].port == 80 and (current.spec.selector or {}) == labels:
            return {"resource": "Service", "name": DEMO, "action": "unchanged", "namespace": LAB_NS}
        if dry_run:
            return {"resource": "Service", "name": DEMO, "action": "would-update", "namespace": LAB_NS}
        current.spec.selector = labels
        facade.core.patch_namespaced_service(DEMO, LAB_NS, current)
        return {"resource": "Service", "name": DEMO, "action": "updated", "namespace": LAB_NS}
    except ApiException as exc:
        if exc.status != 404:
            raise APIError(f"service ensure failed: {exc.reason}", status_code=exc.status) from exc
    if dry_run:
        return {"resource": "Service", "name": DEMO, "action": "would-create", "namespace": LAB_NS}
    body = client.V1Service(
        metadata=client.V1ObjectMeta(name=DEMO, namespace=LAB_NS, labels=labels),
        spec=client.V1ServiceSpec(
            selector=labels,
            ports=[client.V1ServicePort(port=80, target_port=80)],
            type="ClusterIP",
        ),
    )
    facade.core.create_namespaced_service(LAB_NS, body)
    return {"resource": "Service", "name": DEMO, "action": "created", "namespace": LAB_NS}


def ensure_demo_stack(
    facade: KubernetesFacade,
    *,
    message: str = "hello-automation",
    replicas: int = 1,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    return [
        ensure_demo_configmap(facade, message=message, dry_run=dry_run),
        ensure_demo_deployment(facade, replicas=replicas, dry_run=dry_run),
        ensure_demo_service(facade, dry_run=dry_run),
    ]


def delete_demo_stack(facade: KubernetesFacade, *, confirm: bool, dry_run: bool = False) -> list[dict[str, Any]]:
    if not confirm and not dry_run:
        raise ValidationError("delete requires --confirm")
    results = []
    for kind, name, deleter in (
        ("Deployment", DEMO, lambda: facade.apps.delete_namespaced_deployment(DEMO, LAB_NS)),
        ("Service", DEMO, lambda: facade.core.delete_namespaced_service(DEMO, LAB_NS)),
        ("ConfigMap", DEMO_CM, lambda: facade.core.delete_namespaced_config_map(DEMO_CM, LAB_NS)),
    ):
        try:
            if dry_run:
                results.append({"resource": kind, "name": name, "action": "would-delete"})
                continue
            deleter()
            results.append({"resource": kind, "name": name, "action": "deleted"})
        except ApiException as exc:
            if exc.status == 404:
                results.append({"resource": kind, "name": name, "action": "absent"})
            else:
                raise APIError(f"delete {kind} failed: {exc.reason}", status_code=exc.status) from exc
    return results


def patch_vs_replace_note() -> str:
    return (
        "patch: change selected fields (preferred for automation-lab updates). "
        "replace: submit the full desired object — avoid against production resources."
    )
