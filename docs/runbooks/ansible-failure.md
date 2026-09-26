# Runbook: Ansible Failure (Project 1 — Section 26)

**Scope:** Playbooks, inventory, collections, Ansible Runner under `automation/ansible`.  
**Execution environment:** Prefer **Linux / Jenkins `linux-agent`** for playbook runs. **Windows Ansible CLI is blocked** on this workstation — use WSL, Jenkins, or Python Runner wrappers for live execution; local `--syntax-check` may still work where documented.

**Peer runbooks:** [`python-automation-failure.md`](./python-automation-failure.md) · [`automation-failure.md`](./automation-failure.md)

---

## Symptoms

- Runner/playbook non-zero  
- `unreachable` hosts  
- `changed` every run (non-idempotent)  
- ansible-lint CI failure  
- Accidental targeting of `vmware_workers`

---

## Checks

```bash
cd automation/ansible
ansible --version
ansible-inventory -i inventory/hosts.yml --list
ansible lab -i inventory/hosts.yml -m ansible.builtin.ping
ansible-playbook -i inventory/hosts.yml playbooks/<play>.yml --syntax-check
ansible-playbook -i inventory/hosts.yml playbooks/<play>.yml --check --diff
ansible-lint
```

Ensure collections installed: `ansible-galaxy collection install -r collections/requirements.yml -p collections`.

---

## Common failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Missing collection/FQCN | module not found / lint | Install pins; use FQCN |
| Wrong inventory group | unexpected hosts | Fix hosts.yml; confirm `lab` vs workers |
| Readonly worker mutation blocked/needed | `lab_readonly` / policy | Do **not** mutate workers—use localhost |
| Vault unlock failed | decrypt error | Fix CI credential/env—never commit password |
| Non-idempotent shell | always `changed` | Replace with state modules / guards |
| Partial serial failure | some hosts failed | Fix failed batch; re-run; exit was partial |

---

## Runner-specific

- Inspect event stream for failed task name + msg  
- Confirm private data dir cleanup  
- Align Runner timeout with CLI `--timeout`  
- Do not parse only stdout colors

---

## Recovery

1. `--check --diff` until clean.  
2. Apply to **localhost lab** only.  
3. Python verify after Runner.  
4. If play mutated the wrong thing: stop, snapshot evidence, follow rollback—**never** “fix” `platform-lab` via Ansible apply.

---

## Related

[ansible-platform-automation](../automation/ansible-platform-automation.md) · [automation-failure](./automation-failure.md)
