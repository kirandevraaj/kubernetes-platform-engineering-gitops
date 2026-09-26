"""Input validation before calling external systems."""

from __future__ import annotations

import re

from platform_automation.config import ALLOWED_CLUSTERS, ALLOWED_ENVIRONMENTS, LAB_NAMESPACES
from platform_automation.errors import ValidationError

_DNS_LABEL = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
_K8S_NAME = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")
_REGION = re.compile(r"^[a-z]{2}-[a-z]+-\d+$")
_RESOURCE_ID = re.compile(r"^[A-Za-z0-9:./_-]{1,256}$")

# Lab mutation allowlist — refuse arbitrary destructive targets
ALLOWED_MUTATION_NAMESPACES = frozenset({"automation-lab"})
ALLOWED_MUTATION_NAMES = frozenset(
    {
        "automation-demo",
        "automation-demo-config",
        "automation-lab-reader",
        "automation-lab-reader-role",
        "automation-lab-reader-binding",
    }
)
ALLOWED_TAG_MARKERS = frozenset({"automation-lab", "platform-automation-lab"})


def require_environment(value: str) -> str:
    if value not in ALLOWED_ENVIRONMENTS:
        raise ValidationError(f"invalid environment: {value}")
    return value


def require_cluster(value: str) -> str:
    if value not in ALLOWED_CLUSTERS:
        raise ValidationError(f"invalid cluster: {value}")
    return value


def require_namespace(value: str, *, mutation: bool = False) -> str:
    if not _DNS_LABEL.match(value) or len(value) > 63:
        raise ValidationError(f"invalid namespace: {value}")
    if mutation and value not in ALLOWED_MUTATION_NAMESPACES:
        raise ValidationError(
            f"mutations restricted to {sorted(ALLOWED_MUTATION_NAMESPACES)}; got {value}"
        )
    return value


def require_resource_name(value: str, *, mutation: bool = False) -> str:
    if not _K8S_NAME.match(value) or len(value) > 253:
        raise ValidationError(f"invalid resource name: {value}")
    if mutation and value not in ALLOWED_MUTATION_NAMES:
        raise ValidationError(f"resource {value!r} is not on the mutation allowlist")
    return value


def require_region(value: str) -> str:
    if not _REGION.match(value):
        raise ValidationError(f"invalid AWS region: {value}")
    return value


def require_resource_id(value: str) -> str:
    if not _RESOURCE_ID.match(value):
        raise ValidationError(f"invalid resource id: {value}")
    return value


def require_confirm(confirm: bool, action: str) -> None:
    if not confirm:
        raise ValidationError(f"{action} requires --confirm")


def require_lab_namespace_hint(namespace: str) -> None:
    if namespace not in LAB_NAMESPACES and namespace not in ALLOWED_MUTATION_NAMESPACES:
        # Read of other namespaces is allowed; warn via exception only for mutations elsewhere
        return


def require_lab_namespace(namespace: str) -> str:
    return require_namespace(namespace, mutation=True)


def require_lab_resource(name: str) -> str:
    return require_resource_name(name, mutation=True)
