# Runbook: Automation Failure (Project 1)

**Scope:** End-to-end `platform-automate` (or equivalent) runs spanning Python + adapters.  
**Safe NS:** `automation-lab` · **Do not** “fix” by mutating `platform-lab`.

---

## Symptoms

- Non-zero exit (`2` config, `3` auth, `4` verify FAIL, `5` partial, `124` timeout)
- Jenkins automation stage red
- Report shows phase stuck (discover/plan/apply/verify)
- Some adapters OK, others failed

---

## Triage order

1. **Read the report artifact** (`run_id`, phase, exit code, per-resource results).  
2. **Reproduce doctor:** `platform-automate doctor` / inventory read-only.  
3. **Confirm context & environment allow-lists** (`ckad-lab` vs AWS tools; namespace `automation-lab`).  
4. **Classify:** config vs auth vs tool vs verify vs partial.  
5. **Open the specific runbook** (Python / Ansible / AWS / Kubernetes) for the failing adapter.  
6. **Do not** kubectl-apply `platform-lab` or disable Argo self-heal to “make it green.”

---

## Common causes

| Cause | Signal | Action |
|-------|--------|--------|
| Wrong kube context | 403 or unexpected namespaces | `--context` / kubeconfig; re-doctor |
| Bad AWS profile | `AccessDenied` / `ExpiredToken` | Fix profile/region; sts identity |
| Missing pin/venv | ImportError | Recreate `.venv` from requirements |
| Ansible play failed | Runner failed events | [ansible-failure](./ansible-failure.md) |
| Verify timeout | UNKNOWN / 124 | Increase budget or fix underlying Ready |
| Partial host failure | exit 5 | Fix failed targets; re-run idempotently |

---

## Recovery

1. Leave cluster/Git desired state consistent—prefer **re-run idempotent reconcile** after fix, not manual snowflake edits on GitOps apps.  
2. If lab objects half-applied: run `plan` then `reconcile --confirm` or documented rollback.  
3. Archive failing report before retry for audit.  
4. If Git was incorrectly changed: revert commit; let Argo sync.

---

## Escalation evidence

- Command line + flags (redact secrets)  
- Exit code + report JSON  
- kube context / AWS account id (not keys)  
- Jenkins build URL  

---

## Related

[python-automation](./python-automation.md) · [ansible-failure](./ansible-failure.md) · [aws-api-failure](./aws-api-failure.md) · [kubernetes-api-failure](./kubernetes-api-failure.md)
