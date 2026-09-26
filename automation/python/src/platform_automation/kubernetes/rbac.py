"""Minimal RBAC for automation-lab — read allowed, write denied."""

from __future__ import annotations

from typing import Any

from kubernetes import client
from kubernetes.client.rest import ApiException

from platform_automation.errors import APIError
from platform_automation.kubernetes.client import KubernetesFacade

NS = "automation-lab"
SA = "automation-lab-reader"
ROLE = "automation-lab-reader"
BINDING = "automation-lab-reader-binding"


def ensure_reader_rbac(facade: KubernetesFacade, *, dry_run: bool = False) -> list[dict[str, Any]]:
    results = []
    # Namespace must exist
    try:
        facade.core.read_namespace(NS)
    except ApiException as exc:
        if exc.status == 404:
            if dry_run:
                return [{"action": "would-create-namespace", "name": NS}]
            facade.core.create_namespace(
                client.V1Namespace(metadata=client.V1ObjectMeta(name=NS))
            )
        else:
            raise APIError(str(exc.reason), status_code=exc.status) from exc

    sa_body = client.V1ServiceAccount(metadata=client.V1ObjectMeta(name=SA, namespace=NS))
    role_body = client.V1Role(
        metadata=client.V1ObjectMeta(name=ROLE, namespace=NS),
        rules=[
            client.V1PolicyRule(
                api_groups=[""],
                resources=["pods", "services", "configmaps"],
                verbs=["get", "list", "watch"],
            ),
            client.V1PolicyRule(
                api_groups=["apps"],
                resources=["deployments"],
                verbs=["get", "list", "watch"],
            ),
        ],
    )
    binding_body = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name=BINDING, namespace=NS),
        role_ref=client.V1RoleRef(api_group="rbac.authorization.k8s.io", kind="Role", name=ROLE),
        subjects=[client.RbacV1Subject(kind="ServiceAccount", name=SA, namespace=NS)],
    )

    for kind, name, read, create in (
        (
            "ServiceAccount",
            SA,
            lambda: facade.core.read_namespaced_service_account(SA, NS),
            lambda: facade.core.create_namespaced_service_account(NS, sa_body),
        ),
        (
            "Role",
            ROLE,
            lambda: client.RbacAuthorizationV1Api(facade.api_client).read_namespaced_role(ROLE, NS),
            lambda: client.RbacAuthorizationV1Api(facade.api_client).create_namespaced_role(NS, role_body),
        ),
        (
            "RoleBinding",
            BINDING,
            lambda: client.RbacAuthorizationV1Api(facade.api_client).read_namespaced_role_binding(
                BINDING, NS
            ),
            lambda: client.RbacAuthorizationV1Api(facade.api_client).create_namespaced_role_binding(
                NS, binding_body
            ),
        ),
    ):
        try:
            read()
            results.append({"resource": kind, "name": name, "action": "unchanged"})
        except ApiException as exc:
            if exc.status != 404:
                raise APIError(str(exc.reason), status_code=exc.status) from exc
            if dry_run:
                results.append({"resource": kind, "name": name, "action": "would-create"})
            else:
                create()
                results.append({"resource": kind, "name": name, "action": "created"})
    return results


def can_i(facade: KubernetesFacade, verb: str, resource: str, namespace: str = NS) -> bool:
    """Self-subject access review for the current kubeconfig identity."""
    auth = client.AuthorizationV1Api(facade.api_client)
    body = client.V1SelfSubjectAccessReview(
        spec=client.V1SelfSubjectAccessReviewSpec(
            resource_attributes=client.V1ResourceAttributes(
                namespace=namespace,
                verb=verb,
                resource=resource,
            )
        )
    )
    try:
        review = auth.create_self_subject_access_review(body)
    except ApiException as exc:
        raise APIError(f"access review failed: {exc.reason}", status_code=exc.status) from exc
    return bool(review.status and review.status.allowed)
