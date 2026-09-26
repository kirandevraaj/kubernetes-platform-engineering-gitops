"""Unit tests for configuration, retry, validation, commands, REST, controller."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

from platform_automation.config import Settings, load_settings
from platform_automation.controller import PlatformController
from platform_automation.errors import APIError, AutomationTimeoutError, ValidationError
from platform_automation.logging import redact
from platform_automation.retry import is_transient, retry
from platform_automation.rest import ApiClient
from platform_automation.validation import require_namespace, require_region, require_resource_name


@pytest.mark.unit
def test_settings_defaults():
    s = load_settings()
    assert s.environment == "vmware"
    assert s.cluster == "ckad-lab"
    assert s.namespace == "automation-lab"


@pytest.mark.unit
def test_settings_precedence_cli_over_env(monkeypatch, tmp_path):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("environment: aws\ncluster: platform-lab-aws\nregion: us-west-2\n", encoding="utf-8")
    monkeypatch.setenv("PLATFORM_AUTOMATION_NAMESPACE", "security-lab")
    s = load_settings(
        config_path=str(cfg),
        cli_overrides={"namespace": "automation-lab", "region": "eu-west-1"},
    )
    assert s.environment == "aws"
    assert s.cluster == "platform-lab-aws"
    assert s.namespace == "automation-lab"  # CLI wins over env
    assert s.region == "eu-west-1"  # CLI wins over YAML


@pytest.mark.unit
def test_rejects_secrets_in_yaml(tmp_path):
    cfg = tmp_path / "bad.yaml"
    cfg.write_text("password: hunter2\n", encoding="utf-8")
    with pytest.raises(Exception):
        load_settings(config_path=str(cfg))


@pytest.mark.unit
def test_retry_immediate_success():
    assert retry(lambda: 42, max_attempts=3) == 42


@pytest.mark.unit
def test_retry_then_success():
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise APIError("temp", retryable=True)
        return "ok"

    assert retry(flaky, max_attempts=5, base_delay=0.01, jitter=0) == "ok"
    assert state["n"] == 3


@pytest.mark.unit
def test_retry_exhaustion():
    def always():
        raise APIError("temp", retryable=True)

    with pytest.raises(APIError):
        retry(always, max_attempts=2, base_delay=0.01, jitter=0)


@pytest.mark.unit
def test_retry_timeout():
    def always():
        raise APIError("temp", retryable=True)

    with pytest.raises(AutomationTimeoutError):
        retry(always, max_attempts=50, base_delay=0.05, jitter=0, deadline=0.08)


@pytest.mark.unit
def test_does_not_retry_permanent():
    calls = {"n": 0}

    def permanent():
        calls["n"] += 1
        raise APIError("nope", retryable=False)

    with pytest.raises(APIError):
        retry(permanent, max_attempts=5, base_delay=0.01)
    assert calls["n"] == 1
    assert not is_transient(APIError("x", retryable=False))


@pytest.mark.unit
def test_validation_namespace_mutation():
    require_namespace("automation-lab", mutation=True)
    with pytest.raises(ValidationError):
        require_namespace("platform-lab", mutation=True)


@pytest.mark.unit
def test_validation_region_and_name():
    require_region("us-east-1")
    with pytest.raises(ValidationError):
        require_region("US_EAST")
    require_resource_name("automation-demo", mutation=True)
    with pytest.raises(ValidationError):
        require_resource_name("platform-lab", mutation=True)


@pytest.mark.unit
def test_redact_secrets():
    text = "password=secret token=abc123"
    out = redact(text)
    assert "password=secret" not in out
    assert "REDACTED" in out


@pytest.mark.unit
def test_run_command_argv(monkeypatch):
    from platform_automation import commands

    class FakeCompleted:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr(commands.subprocess, "run", lambda *a, **k: FakeCompleted())
    result = commands.run_command(["echo", "hi"], timeout=5)
    assert result.ok
    assert result.stdout == "ok"


@pytest.mark.unit
def test_api_client_get_mocked():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"hello": "world"}, headers={"X-Request-Id": "req-1"})

    transport = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    client = ApiClient("http://test", transport=transport, max_retries=1)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json_body == {"hello": "world"}
    assert resp.request_id == "req-1"
    client.close()


@pytest.mark.unit
def test_api_client_retryable():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 2:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json={"ok": True})

    transport = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    client = ApiClient("http://test", transport=transport, max_retries=3)
    resp = client.get("/flaky")
    assert resp.json_body == {"ok": True}
    client.close()


@pytest.mark.unit
def test_controller_plan_and_check():
    k8s = MagicMock()
    k8s.list_nodes.return_value = [{"name": "n1", "status": "Ready"}]
    k8s.list_namespaces.return_value = ["automation-lab"]
    k8s.list_pods.return_value = [{"name": "automation-demo-x", "ready": True}]
    ctl = PlatformController(settings=Settings(), k8s=k8s)
    plan = ctl.plan()
    assert "desired" in plan
    check = ctl.check()
    assert check["compliance"] == "COMPLIANT"


@pytest.mark.unit
def test_controller_apply_requires_confirm():
    k8s = MagicMock()
    ctl = PlatformController(settings=Settings(confirm=False, dry_run=False), k8s=k8s)
    with pytest.raises(ValidationError):
        ctl.apply()


@pytest.mark.unit
def test_cli_version():
    from platform_automation.cli import main

    assert main(["version"]) == 0


@pytest.mark.unit
def test_terraform_refuses_auto_approve():
    from platform_automation.terraform import refuse_auto_approve

    with pytest.raises(ValidationError):
        refuse_auto_approve(["apply", "-auto-approve"])


@pytest.mark.unit
def test_cache_ttl():
    from platform_automation.cache import TtlCache

    c = TtlCache(default_ttl=60)
    c.set("nodes", [1, 2, 3])
    assert c.get("nodes") == [1, 2, 3]
    with pytest.raises(ValueError):
        c.set("aws_token", "secret")


@pytest.mark.unit
def test_observability_report(tmp_path):
    from platform_automation.observability import new_operation, write_report

    rec = new_operation("test", "ckad-lab", "unit", environment="vmware")
    rec.finish("OK")
    path = write_report(rec, str(tmp_path))
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["status"] == "OK"
    assert "operation_id" in data
