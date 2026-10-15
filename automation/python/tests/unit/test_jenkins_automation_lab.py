"""Static checks for jenkins/Jenkinsfile.automation-lab and jenkins/scripts/run_check.py.

There is no Jenkins controller in CI, so these tests pin the pipeline contract:
no failure masking, real CLI commands and flag positions, required tools that
the pinned dev extras actually install, and offline-by-default cluster stages.
"""

from __future__ import annotations

import importlib.util
import re
import shlex
import sys
import tomllib
from pathlib import Path

import pytest

from platform_automation.cli import build_parser

pytestmark = pytest.mark.unit

REPO = Path(__file__).resolve().parents[4]
JENKINSFILE = REPO / "jenkins" / "Jenkinsfile.automation-lab"
RUN_CHECK = REPO / "jenkins" / "scripts" / "run_check.py"
PYPROJECT = REPO / "automation" / "python" / "pyproject.toml"

TOOL_PACKAGES = {
    "ruff": "ruff",
    "mypy": "mypy",
    "pytest": "pytest",
    "ansible-lint": "ansible-lint",
    "ansible-galaxy": "ansible-core",
}


def _load_run_check():
    spec = importlib.util.spec_from_file_location("run_check", RUN_CHECK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


run_check = _load_run_check()


def _pipeline() -> str:
    """Pipeline source without full-line // comments (which may quote `|| true`)."""
    lines = JENKINSFILE.read_text(encoding="utf-8").splitlines()
    return "\n".join(line for line in lines if not line.lstrip().startswith("//"))


def _shell_commands(text: str) -> list[str]:
    """Join backslash-continued shell lines from every sh ''' block."""
    commands: list[str] = []
    for block in re.findall(r"sh '''(.*?)'''", text, flags=re.S):
        joined = re.sub(r"\\\n\s*", " ", block)
        commands.extend(line.strip() for line in joined.splitlines() if line.strip())
    return commands


def _stage_body(text: str, name: str) -> str:
    start = text.index(f"stage('{name}')")
    following = text.find("stage('", start + 1)
    return text[start : following if following != -1 else len(text)]


# --- no failure masking -----------------------------------------------------------------


@pytest.mark.parametrize(
    "pattern", [r"\|\|\s*true", r"\|\|\s*:", r"catchError", r"returnStatus", r"set \+e"]
)
def test_pipeline_does_not_mask_failures(pattern):
    assert not re.search(pattern, _pipeline()), pattern


def test_every_shell_block_fails_fast():
    blocks = re.findall(r"sh '''(.*?)'''", _pipeline(), flags=re.S)
    assert blocks
    for block in blocks:
        assert block.strip().startswith("set -eu"), block


# --- commands exist and flags are accepted where the pipeline puts them -----------------


def test_platform_automate_commands_parse_with_the_real_cli():
    parser = build_parser()
    commands = [c for c in _shell_commands(_pipeline()) if c.startswith("platform-automate ")]
    assert len(commands) >= 8
    for command in commands:
        argv = shlex.split(command.replace('"${KUBE_TIMEOUT_SECONDS}"', "20"))[1:]
        parser.parse_args(argv)


def test_cluster_commands_are_bounded_and_mutation_only_in_live_stage():
    text = _pipeline()
    cluster = _shell_commands(_stage_body(text, "Cluster dry-run (automation-lab API, read-only)"))
    live = _shell_commands(_stage_body(text, "Live lab (gated)"))
    offline = [
        c
        for c in _shell_commands(text)
        if c.startswith("platform-automate ") and c not in cluster and c not in live
    ]
    assert offline == ["platform-automate version", "platform-automate doctor"]
    for command in cluster + live:
        if command.startswith("platform-automate ") and command != "platform-automate report":
            assert "--timeout" in command, command
    assert all("--confirm" not in c for c in cluster + offline)
    assert any("--dry-run" in c and "ensure" in c for c in cluster)
    assert sum("--confirm" in c for c in live) == 1


def test_cluster_stages_are_parameter_gated_and_default_off():
    text = _pipeline()
    for name in ("RUN_CLUSTER_DRY_RUN", "RUN_LIVE_LAB"):
        assert re.search(rf"name: '{name}',\s*defaultValue: false", text), name
    assert "params.RUN_CLUSTER_DRY_RUN || params.RUN_LIVE_LAB" in _stage_body(
        text, "Cluster dry-run (automation-lab API, read-only)"
    )
    assert "return params.RUN_LIVE_LAB" in _stage_body(text, "Live lab (gated)")


# --- required tools are real and installed by the pinned dev extras ---------------------


def test_checks_are_required_and_tools_come_from_pinned_dev_extras():
    dev = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["optional-dependencies"][
        "dev"
    ]
    pinned = {re.split(r"[=<>\[ ]", spec, maxsplit=1)[0].lower() for spec in dev if "==" in spec}
    checks = [c for c in _shell_commands(_pipeline()) if "run_check.py" in c]
    assert {shlex.split(c)[shlex.split(c).index("--name") + 1] for c in checks} == {
        "ruff",
        "mypy",
        "pytest",
        "ansible-collections",
        "ansible-lint",
    }
    for command in checks:
        argv = shlex.split(command)
        assert "--required" in argv and "--optional" not in argv
        tool = argv[argv.index("--") + 1]
        assert TOOL_PACKAGES[tool] in pinned, f"{tool} must be pinned in the dev extras"


def test_ansible_lint_runs_from_ansible_dir_after_installing_collections():
    body = _shell_commands(_stage_body(_pipeline(), "Ansible lint"))
    install = next(i for i, c in enumerate(body) if "ansible-galaxy collection install" in c)
    lint = next(i for i, c in enumerate(body) if "-- ansible-lint" in c)
    assert install < lint
    assert "--cwd automation/ansible" in body[lint] and "--offline playbooks" in body[lint]
    assert (REPO / "automation" / "ansible" / ".ansible-lint").is_file()


# --- run_check.py statuses -----------------------------------------------------------------


def _run(capsys, *args, **kwargs):
    code = run_check.run_check(*args, **kwargs)
    return code, capsys.readouterr().out


def test_passing_check_reports_passed(capsys):
    code, out = _run(capsys, "noop", [sys.executable, "-c", "pass"], required=True)
    assert code == run_check.PASSED and "noop: PASSED" in out


def test_lint_failure_fails_the_check(capsys, tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("import os\n", encoding="utf-8")
    code, out = _run(
        capsys,
        "ruff",
        [sys.executable, "-m", "ruff", "check", "--isolated", "--select", "F401", str(bad)],
        required=True,
    )
    assert code == run_check.FAILED
    assert "ruff: FAILED" in out and "PASSED" not in out


def test_missing_required_lint_tool_is_a_failure(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    code, out = _run(
        capsys,
        "ansible-lint",
        ["ansible-lint", "--offline", "playbooks"],
        required=True,
        install_hint="pip install -e automation/python[dev]",
    )
    assert code == run_check.MISSING
    assert "MISSING REQUIRED TOOL" in out and "pip install" in out and "PASSED" not in out


def test_missing_optional_tool_is_reported_as_skipped_not_passed(capsys, tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    summary = tmp_path / "summary.txt"
    code, out = _run(
        capsys, "shellcheck", ["shellcheck", "x.sh"], required=False, summary_file=str(summary)
    )
    assert code == run_check.SKIPPED and code != run_check.PASSED
    assert "SKIPPED" in out and "did NOT run" in out and "PASSED" not in out
    assert "SKIPPED" in summary.read_text(encoding="utf-8")


def test_check_timeout_is_a_failure(capsys):
    code, out = _run(
        capsys,
        "slow",
        [sys.executable, "-c", "import time; time.sleep(30)"],
        required=True,
        timeout=1,
    )
    assert code == run_check.FAILED and "timed out" in out


def test_cli_requires_separator_and_mode(capsys):
    assert run_check.main(["--name", "x", "--required", sys.executable]) == run_check.MISSING
    with pytest.raises(SystemExit):
        run_check.main(["--name", "x", "--", sys.executable, "-c", "pass"])
    assert run_check.main(["--name", "x", "--required", "--", sys.executable, "-c", "pass"]) == 0
