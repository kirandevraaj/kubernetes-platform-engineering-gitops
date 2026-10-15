"""CLI flag placement and mutation gates — no cluster, AWS or Ansible access."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from platform_automation import cli
from platform_automation.errors import APIError, AuthenticationError, ValidationError

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    for key in ("PLATFORM_CONFIRM", "PLATFORM_DRY_RUN", "PLATFORM_AUTOMATION_CONFIG"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def no_cluster(monkeypatch):
    def _refuse(_settings):
        raise AssertionError("kubernetes client must not be created")

    monkeypatch.setattr(cli, "_k8s_facade", _refuse)


@pytest.fixture
def fake_cluster(monkeypatch):
    calls: list[dict] = []
    monkeypatch.setattr(cli, "_k8s_facade", lambda _settings: object())

    def _ensure(_facade, *, message, replicas, dry_run):
        calls.append({"message": message, "replicas": replicas, "dry_run": dry_run})
        return [{"resource": "ConfigMap", "action": "would-create" if dry_run else "created"}]

    monkeypatch.setattr("platform_automation.kubernetes.idempotent.ensure_demo_stack", _ensure)
    return calls


@pytest.mark.parametrize(
    "argv",
    [
        ["kubernetes", "ensure", "--dry-run"],
        ["--dry-run", "kubernetes", "ensure"],
        ["platform", "plan", "--dry-run"],
    ],
)
def test_global_flags_accepted_before_or_after_subcommand(argv):
    args = cli.build_parser().parse_args(argv)
    assert args.dry_run is True
    assert args.confirm is False


def test_flag_after_subcommand_does_not_reset_flag_before_it():
    args = cli.build_parser().parse_args(["--confirm", "platform", "apply", "--verbose"])
    assert args.confirm is True
    assert args.verbose is True


def test_subcommand_namespace_options_keep_their_defaults():
    parser = cli.build_parser()
    assert parser.parse_args(["kubernetes", "wait"]).namespace == "automation-lab"
    assert parser.parse_args(["kubernetes", "pods", "--namespace", "kube-system"]).namespace == (
        "kube-system"
    )


def test_kubernetes_ensure_requires_confirm(no_cluster, capsys):
    assert cli.main(["kubernetes", "ensure"]) == ValidationError.exit_code
    assert "--confirm" in capsys.readouterr().err


def test_kubernetes_ensure_dry_run_needs_no_confirm(fake_cluster, capsys):
    assert cli.main(["kubernetes", "ensure", "--dry-run"]) == 0
    assert fake_cluster == [{"message": "hello-automation", "replicas": 1, "dry_run": True}]
    assert json.loads(capsys.readouterr().out)[0]["action"] == "would-create"


def test_kubernetes_ensure_with_confirm_mutates(fake_cluster):
    assert cli.main(["kubernetes", "ensure", "--confirm"]) == 0
    assert fake_cluster[0]["dry_run"] is False


def test_ansible_apply_requires_confirm(monkeypatch, tmp_path, capsys):
    playbook = tmp_path / "site.yml"
    playbook.write_text("- hosts: localhost\n  tasks: []\n", encoding="utf-8")

    def _refuse(*_args, **_kwargs):
        raise AssertionError("playbook must not run without --check or --confirm")

    monkeypatch.setattr("platform_automation.ansible.run_playbook", _refuse)
    assert cli.main(["ansible", "--playbook", str(playbook)]) == ValidationError.exit_code
    assert "--confirm" in capsys.readouterr().err


def test_ansible_check_mode_runs_without_confirm(monkeypatch, tmp_path):
    playbook = tmp_path / "site.yml"
    playbook.write_text("- hosts: localhost\n  tasks: []\n", encoding="utf-8")
    seen: dict = {}

    def _run(path, **kwargs):
        seen.update(kwargs, path=path)
        return SimpleNamespace(rc=0, status="successful", backend="test", duration=0.0, ok=True)

    monkeypatch.setattr("platform_automation.ansible.run_playbook", _run)
    assert cli.main(["ansible", "--playbook", str(playbook), "--check"]) == 0
    assert seen["check"] is True


def test_report_module_imports_and_writes(tmp_path):
    from platform_automation.report import build_report, write_report

    out = write_report("summary", build_report("t", {"a": 1}), report_dir=tmp_path)
    assert out == tmp_path / "summary.json"
    assert json.loads(out.read_text(encoding="utf-8"))["sections"] == {"a": 1}


@pytest.mark.parametrize("name", ["../escape", "nested/name", "", ".."])
def test_report_rejects_path_like_names(tmp_path, name):
    from platform_automation.report import write_report

    with pytest.raises(ValidationError):
        write_report(name, {}, report_dir=tmp_path)


def test_translate_botocore_error_maps_codes():
    from platform_automation.aws.errors import translate_botocore_error

    class FakeClientError(Exception):
        def __init__(self, code: str) -> None:
            super().__init__(f"boom {code}")
            self.response = {"Error": {"Code": code}}

    assert isinstance(translate_botocore_error(FakeClientError("ExpiredToken")), AuthenticationError)
    err = translate_botocore_error(FakeClientError("Throttling"))
    assert isinstance(err, APIError)
    assert "Throttling" in str(err)
    assert isinstance(translate_botocore_error(RuntimeError("plain")), APIError)
