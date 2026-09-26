"""Kubernetes package exports."""

from platform_automation.kubernetes.client import (
    KubernetesFacade,
    get_current_context,
    list_context_names,
    load_api_client,
)
from platform_automation.kubernetes.idempotent import ensure_demo_stack

__all__ = [
    "KubernetesFacade",
    "ensure_demo_stack",
    "get_current_context",
    "list_context_names",
    "load_api_client",
]
