"""Dry-run never mutates; cluster reads are bounded and fail clearly.

Uses in-process fake API servers on 127.0.0.1 and a temporary kubeconfig, so
no real kubeconfig, cluster or network route is involved.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import yaml
from kubernetes.client import Configuration
from kubernetes.client.rest import ApiException

from platform_automation import cli
from platform_automation.errors import APIError, AutomationTimeoutError, ValidationError
from platform_automation.kubernetes import idempotent
from platform_automation.kubernetes.client import BoundedApiClient, KubernetesFacade

pytestmark = pytest.mark.unit

MUTATING_PREFIXES = ("create_", "patch_", "replace_", "delete_")
BOUND_SECONDS = 10.0


class _FakeApi(BaseHTTPRequestHandler):
    """Answers like an empty cluster: /version works, every object is 404."""

    requests: list[tuple[str, str]]

    def _record(self) -> None:
        self.server.requests.append((self.command, self.path))  # type: ignore[attr-defined]

    def _send(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        self._record()
        if self.path.rstrip("/") == "/version":
            self._send(
                200,
                {
                    "major": "1",
                    "minor": "31",
                    "gitVersion": "v1.31.14",
                    "gitCommit": "0" * 40,
                    "gitTreeState": "clean",
                    "buildDate": "2026-01-01T00:00:00Z",
                    "goVersion": "go1.24",
                    "compiler": "gc",
                    "platform": "linux/amd64",
                },
            )
            return
        self._send(
            404,
            {
                "kind": "Status",
                "apiVersion": "v1",
                "status": "Failure",
                "reason": "NotFound",
                "code": 404,
            },
        )

    def _refuse(self) -> None:
        self._record()
        self._send(405, {"kind": "Status", "code": 405})

    do_POST = do_PUT = do_PATCH = do_DELETE = _refuse  # noqa: N815

    def log_message(self, *_args) -> None:
        return


@pytest.fixture
def fake_api():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeApi)
    server.requests = []  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()


@pytest.fixture
def silent_api():
    """Accepts TCP connections and reads requests but never answers."""
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.settimeout(0.2)
    stop = threading.Event()
    seen: list[bytes] = []
    held: list[socket.socket] = []

    def accept() -> None:
        while not stop.is_set():
            try:
                conn, _ = listener.accept()
            except OSError:
                continue
            held.append(conn)
            conn.settimeout(0.5)
            try:
                seen.append(conn.recv(65536).split(b"\r\n", 1)[0])
            except OSError:
                pass

    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    yield SimpleNamespace(port=listener.getsockname()[1], seen=seen)
    stop.set()
    thread.join(timeout=2)
    for conn in held:
        conn.close()
    listener.close()


def _write_kubeconfig(tmp_path, monkeypatch, port: int):
    from kubernetes.config import kube_config

    path = tmp_path / "kubeconfig"
    path.write_text(
        yaml.safe_dump(
            {
                "apiVersion": "v1",
                "kind": "Config",
                "clusters": [{"name": "fake", "cluster": {"server": f"http://127.0.0.1:{port}"}}],
                "users": [{"name": "fake", "user": {"token": "fake-test-token"}}],
                "contexts": [{"name": "ckad-lab", "context": {"cluster": "fake", "user": "fake"}}],
                "current-context": "ckad-lab",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(kube_config, "KUBE_CONFIG_DEFAULT_LOCATION", str(path))


def _mutations(facade) -> list[str]:
    calls = facade.core.method_calls + facade.apps.method_calls
    return [c[0] for c in calls if c[0].startswith(MUTATING_PREFIXES)]


def _mock_facade() -> SimpleNamespace:
    return SimpleNamespace(core=MagicMock(), apps=MagicMock())


def _not_found(*_args, **_kwargs):
    raise ApiException(status=404, reason="Not Found")


# --- ensure --dry-run never calls a mutating method -----------------------------------


def test_dry_run_with_nothing_present_only_reads():
    facade = _mock_facade()
    facade.core.read_namespace.side_effect = _not_found
    facade.core.read_namespaced_config_map.side_effect = _not_found
    facade.apps.read_namespaced_deployment.side_effect = _not_found
    facade.core.read_namespaced_service.side_effect = _not_found

    result = idempotent.ensure_demo_stack(facade, dry_run=True)

    assert [r["action"] for r in result] == ["would-create"] * 3
    assert _mutations(facade) == []


def test_dry_run_with_drifted_objects_only_reads():
    facade = _mock_facade()
    facade.core.read_namespaced_config_map.return_value = SimpleNamespace(data={"message": "old"})
    container = SimpleNamespace(image="example/old:1")
    facade.apps.read_namespaced_deployment.return_value = SimpleNamespace(
        spec=SimpleNamespace(
            replicas=3, template=SimpleNamespace(spec=SimpleNamespace(containers=[container]))
        )
    )
    facade.core.read_namespaced_service.return_value = SimpleNamespace(
        spec=SimpleNamespace(ports=[SimpleNamespace(port=8080)], selector={"app": "other"})
    )

    result = idempotent.ensure_demo_stack(facade, dry_run=True)

    assert [r["action"] for r in result] == ["would-update"] * 3
    assert _mutations(facade) == []


def test_dry_run_read_failure_raises_without_mutating():
    facade = _mock_facade()
    facade.core.read_namespace.side_effect = AutomationTimeoutError("api did not respond")

    with pytest.raises(AutomationTimeoutError):
        idempotent.ensure_demo_stack(facade, dry_run=True)
    assert _mutations(facade) == []


def test_delete_dry_run_makes_no_api_calls():
    facade = _mock_facade()
    result = idempotent.delete_demo_stack(facade, confirm=False, dry_run=True)
    assert {r["action"] for r in result} == {"would-delete"}
    assert facade.core.method_calls == [] and facade.apps.method_calls == []


# --- real client against fake API servers -----------------------------------------------


def test_cli_ensure_dry_run_sends_only_get_requests(fake_api, tmp_path, monkeypatch, capsys):
    _write_kubeconfig(tmp_path, monkeypatch, fake_api.server_port)

    assert cli.main(["kubernetes", "ensure", "--dry-run", "--timeout", "5"]) == 0

    actions = [r["action"] for r in json.loads(capsys.readouterr().out)]
    assert actions == ["would-create"] * 3
    methods = {method for method, _ in fake_api.requests}
    assert methods == {"GET"}, fake_api.requests


def test_cli_ensure_without_confirm_never_contacts_api(fake_api, tmp_path, monkeypatch):
    _write_kubeconfig(tmp_path, monkeypatch, fake_api.server_port)
    assert cli.main(["kubernetes", "ensure"]) == ValidationError.exit_code
    assert fake_api.requests == []


def test_cli_preflight_reports_server_and_namespace(fake_api, tmp_path, monkeypatch, capsys):
    _write_kubeconfig(tmp_path, monkeypatch, fake_api.server_port)

    assert cli.main(["kubernetes", "preflight", "--timeout", "5"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "OK"
    assert payload["server_version"] == "v1.31.14"
    assert payload["namespace"] == "automation-lab"
    assert payload["namespace_state"] == "absent"
    assert payload["context"] == "ckad-lab"
    assert {m for m, _ in fake_api.requests} == {"GET"}


@pytest.mark.parametrize(
    "argv",
    [
        ["--timeout", "1", "kubernetes", "ensure", "--dry-run"],
        ["kubernetes", "preflight", "--timeout", "1"],
        ["platform", "plan", "--timeout", "1"],
    ],
)
def test_unresponsive_api_fails_within_bound(silent_api, tmp_path, monkeypatch, capsys, argv):
    _write_kubeconfig(tmp_path, monkeypatch, silent_api.port)

    started = time.monotonic()
    code = cli.main(argv)
    elapsed = time.monotonic() - started

    assert code == AutomationTimeoutError.exit_code
    assert elapsed < BOUND_SECONDS
    err = capsys.readouterr().err
    assert "did not respond" in err and "kubernetes preflight" in err
    assert all(line.startswith(b"GET ") for line in silent_api.seen), silent_api.seen


def test_refused_connection_fails_fast_and_clearly():
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    configuration = Configuration(host=f"http://127.0.0.1:{port}")
    # Windows retries refused SYNs for ~2s; keep the connect budget above that.
    facade = KubernetesFacade(api_client=BoundedApiClient(configuration, request_timeout=5))

    started = time.monotonic()
    with pytest.raises((APIError, AutomationTimeoutError)) as excinfo:
        facade.core.read_namespace("automation-lab")
    assert time.monotonic() - started < BOUND_SECONDS
    assert "kubernetes preflight" in str(excinfo.value)
    if sys.platform != "win32":
        # Windows can surface a refused loopback connect as a connect timeout.
        assert isinstance(excinfo.value, APIError)
        assert "unreachable" in str(excinfo.value)
        assert excinfo.value.retryable is True


def test_preflight_maps_forbidden_to_authentication_error():
    from platform_automation.errors import AuthenticationError

    facade = KubernetesFacade(api_client=MagicMock())
    facade.version = MagicMock()
    facade.version.get_code.return_value = SimpleNamespace(git_version="v1.31.14")
    facade.core = MagicMock()
    facade.core.read_namespace.side_effect = ApiException(status=403, reason="Forbidden")
    with pytest.raises(AuthenticationError, match="403"):
        facade.preflight("automation-lab")


def test_bounded_client_disables_hidden_retries_and_sets_timeouts():
    api = BoundedApiClient(Configuration(host="http://127.0.0.1:1"), request_timeout=30)
    assert api.configuration.retries == 0
    assert api.request_timeout == (10.0, 30)
    with pytest.raises(Exception, match="positive"):
        BoundedApiClient(Configuration(host="http://127.0.0.1:1"), request_timeout=0)


# --- plan / verify no longer hide failures -----------------------------------------------


def test_plan_records_api_errors_but_raises_connectivity_errors():
    from platform_automation.config import Settings
    from platform_automation.controller import PlatformController

    k8s = MagicMock()
    k8s.list_pods.side_effect = ApiException(status=403, reason="Forbidden")
    assert "403" in PlatformController(settings=Settings(), k8s=k8s).plan()["actual"]["error"]

    k8s.list_pods.side_effect = AutomationTimeoutError("api did not respond")
    with pytest.raises(AutomationTimeoutError):
        PlatformController(settings=Settings(), k8s=k8s).plan()


@pytest.mark.parametrize(
    ("pods", "expected"),
    [
        ([{"name": "automation-demo-1", "ready": True}], 0),
        ([{"name": "automation-demo-1", "ready": False}], 4),
        ([], 4),
    ],
)
def test_platform_verify_exit_code_reflects_status(monkeypatch, pods, expected):
    k8s = MagicMock()
    k8s.list_pods.return_value = pods
    monkeypatch.setattr(cli, "_k8s_facade", lambda _settings: k8s)
    assert cli.main(["platform", "verify"]) == expected


# --- offline isolation -------------------------------------------------------------------


def test_unit_tests_cannot_load_a_real_kubeconfig():
    from platform_automation.errors import AuthenticationError
    from platform_automation.kubernetes.client import load_api_client

    with pytest.raises(AuthenticationError, match="kubeconfig"):
        load_api_client("ckad-lab")


def test_unit_tests_have_no_aws_credentials():
    import boto3

    assert boto3.Session().get_credentials() is None


def test_doctor_is_offline_without_kubeconfig(capsys):
    assert cli.main(["doctor"]) == 0
    assert json.loads(capsys.readouterr().out)["kubernetes"]["status"] == "ERROR"
