"""CRUD helpers restricted to automation-lab namespace."""

from __future__ import annotations

from typing import Any

from platform_automation.errors import ValidationError
from platform_automation.validation import require_lab_namespace, require_lab_resource

DEMO_DEPLOYMENT = "automation-demo"
DEMO_SERVICE = "automation-demo"
DEMO_CONFIGMAP = "automation-demo-config"


def _body_deployment(name: str, namespace: str) -> dict[str, Any]:
    return {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"app": name, "lab": "automation-lab"},
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "containers": [
                        {
                            "name": "demo",
                            "image": "nginx:1.27-alpine",
                            "ports": [{"containerPort": 80}],
                        }
                    ]
                },
            },
        },
    }


def _body_service(name: str, namespace: str) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"app": name, "lab": "automation-lab"},
        },
        "spec": {
            "selector": {"app": name},
            "ports": [{"port": 80, "targetPort": 80}],
        },
    }


def _body_configmap(name: str, namespace: str) -> dict[str, Any]:
    return {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {"app": DEMO_DEPLOYMENT, "lab": "automation-lab"},
        },
        "data": {"message": "automation-lab"},
    }


def _is_not_found(exc: BaseException) -> bool:
    status = getattr(exc, "status", None)
    if status == 404:
        return True
    # Fallback for plain mocks that raise KeyError/LookupError
    return isinstance(exc, (KeyError, LookupError, FileNotFoundError))


def create_or_get(
    api: Any,
    *,
    create_fn: str,
    read_fn: str,
    body: dict[str, Any],
    namespace: str,
    dry_run: bool = False,
) -> dict[str, Any]:
    require_lab_namespace(namespace)
    name = body["metadata"]["name"]
    require_lab_resource(name)
    kwargs: dict[str, Any] = {"namespace": namespace, "body": body}
    if dry_run:
        kwargs["dry_run"] = "All"
    try:
        getattr(api, read_fn)(name, namespace)
        return {"action": "exists", "name": name, "kind": body.get("kind")}
    except Exception as exc:
        if not _is_not_found(exc):
            raise
        getattr(api, create_fn)(**kwargs)
        return {
            "action": "created" if not dry_run else "dry-run-create",
            "name": name,
            "kind": body.get("kind"),
        }


def delete_namespaced(
    api: Any,
    *,
    delete_fn: str,
    name: str,
    namespace: str,
    dry_run: bool = False,
    confirm: bool = False,
) -> dict[str, Any]:
    require_lab_namespace(namespace)
    require_lab_resource(name)
    if not dry_run and not confirm:
        raise ValidationError("delete requires --confirm unless --dry-run")
    kwargs: dict[str, Any] = {"name": name, "namespace": namespace}
    if dry_run:
        kwargs["dry_run"] = "All"
    getattr(api, delete_fn)(**kwargs)
    return {"action": "deleted" if not dry_run else "dry-run-delete", "name": name}


def ensure_demo_stack(
    core_api: Any,
    apps_api: Any,
    namespace: str = "automation-lab",
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    require_lab_namespace(namespace)
    results = []
    # ConfigMap
    results.append(
        create_or_get(
            core_api,
            create_fn="create_namespaced_config_map",
            read_fn="read_namespaced_config_map",
            body=_body_configmap(DEMO_CONFIGMAP, namespace),
            namespace=namespace,
            dry_run=dry_run,
        )
    )
    results.append(
        create_or_get(
            apps_api,
            create_fn="create_namespaced_deployment",
            read_fn="read_namespaced_deployment",
            body=_body_deployment(DEMO_DEPLOYMENT, namespace),
            namespace=namespace,
            dry_run=dry_run,
        )
    )
    results.append(
        create_or_get(
            core_api,
            create_fn="create_namespaced_service",
            read_fn="read_namespaced_service",
            body=_body_service(DEMO_SERVICE, namespace),
            namespace=namespace,
            dry_run=dry_run,
        )
    )
    return {"namespace": namespace, "resources": results}


def verify_demo_stack(
    core_api: Any,
    apps_api: Any,
    namespace: str = "automation-lab",
) -> dict[str, Any]:
    require_lab_namespace(namespace)
    present = {}
    for kind, read, name, api in [
        ("ConfigMap", "read_namespaced_config_map", DEMO_CONFIGMAP, core_api),
        ("Deployment", "read_namespaced_deployment", DEMO_DEPLOYMENT, apps_api),
        ("Service", "read_namespaced_service", DEMO_SERVICE, core_api),
    ]:
        try:
            getattr(api, read)(name, namespace)
            present[kind] = True
        except Exception:
            present[kind] = False
    return {"namespace": namespace, "present": present, "ok": all(present.values())}
