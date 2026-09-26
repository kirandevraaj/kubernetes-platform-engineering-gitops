# Dry-run / precondition pattern

**Design guidance** for operational automation (Terraform, Python, Ansible, GitOps).

## Pattern

**Check → Plan → Confirm → Execute → Verify**

| Stage | Intent |
|---|---|
| Check | READ-ONLY inventory / doctor / health |
| Plan | Show intended change without applying (`terraform plan`, Ansible `--check`, Git PR diff) |
| Confirm | Human approval; blast radius understood |
| Execute | Smallest approved mutation |
| Verify | Health, Argo Synced/Healthy, HTTP `/health`, PVC Bound |

## Mapping

| Tool | Check | Plan | Execute |
|---|---|---|---|
| Terraform | `validate` | `plan -out=` | apply **saved plan only** |
| Python | `platform-automate doctor` / `ops health` | report / triage | explicit mutate commands only if ever added (ops is READ-ONLY) |
| Ansible | inventory / ping | `--check --diff` | playbook apply on Linux/Jenkins |
| GitOps | Argo status | Git PR / diff | merge → Argo reconcile |

## Principle

Never make an irreversible change before understanding **target** and **impact**.

See [terraform-apply-safety.md](../runbooks/terraform-apply-safety.md) · [operational-antipatterns.md](./operational-antipatterns.md).
