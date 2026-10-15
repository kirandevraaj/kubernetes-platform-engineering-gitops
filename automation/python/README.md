# platform-automation

Section 24 Python platform automation package for the Kubernetes Platform Engineering & GitOps lab.

## Install

```powershell
cd automation/python
.\.venv\Scripts\pip.exe install -e .
```

## CLI

```powershell
.\.venv\Scripts\platform-automate.exe version
.\.venv\Scripts\platform-automate.exe doctor
.\.venv\Scripts\platform-automate.exe --timeout 10 kubernetes preflight
.\.venv\Scripts\platform-automate.exe platform plan
.\.venv\Scripts\platform-automate.exe kubernetes ensure --dry-run
```

`version` and `doctor` are offline. `kubernetes preflight`, `platform plan` and
`kubernetes ensure --dry-run` are read-only but **do** call the Kubernetes API from the
current kubeconfig context; `--dry-run` means "no writes", not "no cluster". Each API call
is bounded by `--timeout` (default 30 s, connect ≤ 10 s, no retries) and an unreachable
API exits 5 (unreachable) or 6 (timed out) instead of hanging. `platform verify` exits 4
when the demo pods are missing or not Ready. See the
[command reference](../../docs/automation/automation-command-reference.md#exit-code-quick-map).

## Safety

- Kubernetes mutations only in namespace `automation-lab`
- Mutating commands (`kubernetes ensure`/`delete`, `platform apply`/`reconcile`, `aws tag-resource`)
  require `--confirm`; use `--dry-run` to preview. `ansible` requires `--check` or `--confirm`.
- Global flags such as `--dry-run` and `--confirm` may be given before or after the subcommand
- Terraform defaults to `plan` only; refuses `-auto-approve` on project infra
- AWS tag mutations require allowlisted `automation-lab` resources + dry-run/confirm
- Never uses `shell=True`

## Tests

```powershell
.\.venv\Scripts\pip.exe install -e ".[dev]"
.\.venv\Scripts\pytest.exe tests/unit -q
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\mypy.exe src
```

GitHub Actions runs the same unit tests, `ruff check` and `mypy` on every pull request
(`.github/workflows/ci.yml`).

Unit tests are offline: `tests/conftest.py` points `KUBECONFIG` and the AWS config and
credential files at missing paths and clears AWS and `PLATFORM_*` variables, so no test can
reach a real cluster or AWS account. Kubernetes behaviour is tested against a local fake
API server (`tests/unit/test_kubernetes_dry_run.py`).

Live tests are skipped unless `--live` is passed.

## Windows Ansible note

`ansible-runner` may fail importing `fcntl` on Windows. The package falls back to
`subprocess` + `ansible-playbook` with the same `run_playbook` / `get_status` API.
