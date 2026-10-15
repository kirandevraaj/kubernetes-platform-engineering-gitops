"""Kubernetes client loading and context selection."""

from __future__ import annotations

from typing import Any

import urllib3
from kubernetes import config
from kubernetes.client import (
    ApiClient,
    AppsV1Api,
    AutoscalingV1Api,
    Configuration,
    CoreV1Api,
    VersionApi,
)
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException

from platform_automation.errors import (
    APIError,
    AuthenticationError,
    AutomationTimeoutError,
    ConfigurationError,
)

DEFAULT_REQUEST_TIMEOUT = 30.0
MAX_CONNECT_TIMEOUT = 10.0

_TROUBLESHOOT = (
    "Check the kubeconfig context, VPN/network route and API server health; "
    "`platform-automate --context <name> kubernetes preflight` repeats this read-only check."
)


class BoundedApiClient(ApiClient):
    """ApiClient that applies a default timeout to every call and fails clearly.

    The upstream client defaults to no timeout and three silent urllib3 retries,
    so an unreachable API server can block a CLI run for minutes.
    """

    def __init__(
        self,
        configuration: Configuration | None = None,
        *,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
        context: str | None = None,
    ) -> None:
        if request_timeout <= 0:
            raise ConfigurationError(f"request timeout must be positive, got {request_timeout}")
        configuration = configuration or Configuration.get_default_copy()
        configuration.retries = 0
        super().__init__(configuration)
        self.request_timeout = (min(request_timeout, MAX_CONNECT_TIMEOUT), request_timeout)
        self.context = context

    @property
    def host(self) -> str:
        return str(self.configuration.host)

    def call_api(self, *args: Any, **kwargs: Any) -> Any:
        if kwargs.get("_request_timeout") is None:
            kwargs["_request_timeout"] = self.request_timeout
        try:
            return super().call_api(*args, **kwargs)
        except urllib3.exceptions.HTTPError as exc:
            raise _unreachable(exc, self.host, self.context, self.request_timeout) from exc


def _unreachable(
    exc: urllib3.exceptions.HTTPError,
    host: str,
    context: str | None,
    timeout: tuple[float, float],
) -> APIError | AutomationTimeoutError:
    reason = getattr(exc, "reason", None) or exc
    where = f"Kubernetes API {host}" + (f" (context {context})" if context else "")
    if isinstance(reason, urllib3.exceptions.TimeoutError) or isinstance(
        exc, urllib3.exceptions.TimeoutError
    ):
        return AutomationTimeoutError(
            f"{where} did not respond within {timeout[0]:g}s connect / {timeout[1]:g}s read. "
            f"{_TROUBLESHOOT}"
        )
    return APIError(
        f"{where} is unreachable: {reason.__class__.__name__}. {_TROUBLESHOOT}", retryable=True
    )


def load_api_client(
    context: str | None = None, *, request_timeout: float = DEFAULT_REQUEST_TIMEOUT
) -> BoundedApiClient:
    configuration = Configuration()
    try:
        config.load_kube_config(context=context or None, client_configuration=configuration)
    except ConfigException as exc:
        raise AuthenticationError(
            f"failed to load kubeconfig{f' context {context!r}' if context else ''}: {exc}. "
            "Set KUBECONFIG or --context; offline commands (doctor, version, dr, ops triage) "
            "do not need a cluster."
        ) from exc
    return BoundedApiClient(configuration, request_timeout=request_timeout, context=context)


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

    def __init__(
        self,
        api_client: ApiClient | None = None,
        context: str | None = None,
        *,
        request_timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> None:
        self.api_client = api_client or load_api_client(context, request_timeout=request_timeout)
        self.core = CoreV1Api(self.api_client)
        self.apps = AppsV1Api(self.api_client)
        self.autoscaling = AutoscalingV1Api(self.api_client)
        self.version = VersionApi(self.api_client)

    def preflight(self, namespace: str) -> dict[str, Any]:
        """Read-only reachability and permission check for one namespace."""
        try:
            server = self.version.get_code()
        except ApiException as exc:
            raise _api_failure(exc, "read server version") from exc
        try:
            self.core.read_namespace(namespace)
            namespace_state = "present"
        except ApiException as exc:
            if exc.status != 404:
                raise _api_failure(exc, f"read namespace {namespace!r}") from exc
            namespace_state = "absent"
        return {
            "status": "OK",
            "host": getattr(self.api_client.configuration, "host", None),
            "server_version": getattr(server, "git_version", None),
            "namespace": namespace,
            "namespace_state": namespace_state,
        }

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


def _api_failure(exc: ApiException, action: str) -> AuthenticationError | APIError:
    if exc.status in (401, 403):
        return AuthenticationError(
            f"{action} denied (HTTP {exc.status}); check the context's credentials and RBAC"
        )
    return APIError(f"{action} failed: HTTP {exc.status} {exc.reason}", status_code=exc.status)


def _pod_ready(pod: Any) -> bool:
    if not pod.status or not pod.status.conditions:
        return False
    return any(c.type == "Ready" and c.status == "True" for c in pod.status.conditions)
