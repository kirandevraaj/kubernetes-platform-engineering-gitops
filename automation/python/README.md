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
.\.venv\Scripts\platform-automate.exe platform plan --dry-run
```

## Safety

- Kubernetes mutations only in namespace `automation-lab`
- Destructive ops require `--confirm`
- Terraform defaults to `plan` only; refuses `-auto-approve` on project infra
- AWS tag mutations require allowlisted `automation-lab` resources + dry-run/confirm
- Never uses `shell=True`

## Tests

```powershell
.\.venv\Scripts\pytest.exe tests/unit -q
```

Live tests are skipped unless `--live` is passed.

## Windows Ansible note

`ansible-runner` may fail importing `fcntl` on Windows. The package falls back to
`subprocess` + `ansible-playbook` with the same `run_playbook` / `get_status` API.
