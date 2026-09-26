# Runbook: Python Automation (Project 1)

**Scope:** Python runtime, CLI, config, subprocess, retries/timeouts inside `automation/python`.

---

## Symptoms

- `ImportError` / wrong package versions  
- CLI exits `2` on validation  
- `TimeoutExpired` from subprocess  
- Hung runs without logs  
- Tests pass locally but CI fails (venv drift)

---

## Checks

```powershell
cd automation\python
.\.venv\Scripts\Activate.ps1
python --version          # expect 3.14.x
pip show kubernetes boto3 ansible-runner
pytest -q
ruff check .
```

Confirm pins: `kubernetes==32.0.1`, `boto3==1.40.18`, `ansible-runner==2.4.1`.

---

## Common failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Unactivated venv | system python, missing modules | Activate/recreate venv |
| Invalid config/namespace | exit 2 before API | Fix flags/config allow-list |
| `shell=True` breakage | injection/quoting bugs | Switch to argv list |
| No timeout | Jenkins hung | Add `--timeout` / subprocess timeout |
| Retry storm on 403 | repeated AccessDenied | Stop retry; fix auth |
| Logging secrets | credential in console | Rotate; redact; fix logger |

---

## Safe retry pattern

1. Fix root cause (config/auth/deps).  
2. Re-run `doctor` → `plan --dry-run`.  
3. Only then `reconcile --confirm` on `automation-lab`.  
4. `verify` must PASS (not UNKNOWN ignored as success).

---

## What not to do

- Blindly `pip install -U` everything  
- Catch-all `except:` and exit 0  
- Bypass `--confirm` with ad-hoc scripts against `platform-lab`

---

## Related

[automation-failure](./automation-failure.md) · [python fundamentals](../python-automation-fundamentals.md)
