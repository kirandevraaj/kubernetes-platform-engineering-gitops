# Ansible variable precedence (lab)

Status: learning reference for Section 24. Harmless demo only — no cluster or cloud mutations.

Ansible resolves a variable name by walking a fixed precedence ladder. **Later wins.**  
The lab variable `precedence_demo_value` is set in multiple places so you can see which source wins.

## Order (simplified, low → high)

| Priority | Source | Lab example |
|---|---|---|
| 1 (lowest) | Role defaults | `roles/*/defaults/main.yml` |
| 2 | Inventory `group_vars/all` | `inventory/group_vars/all.yml` → `all` |
| 3 | Inventory `group_vars/<group>` | `inventory/group_vars/lab.yml` → `lab` |
| 4 | Inventory `host_vars/<host>` | `inventory/host_vars/` (optional) |
| 5 | Play `vars:` / `vars_files` / `include_vars` | `playbooks/01_basics.yml` → `play` |
| 6 | Role `vars/main.yml` | role constants (beat role defaults) |
| 7 | Block / task `vars` | task-scoped |
| 8 | Extra vars (`-e` / `--extra-vars`) | **highest** → e.g. `extra` |

> Full upstream list includes registered vars, set_fact, include_vars timing, and more. For interviews, remember: **role defaults are weak; `--extra-vars` always wins.**

## Harmless demo

Files:

- `inventory/group_vars/all.yml` — `precedence_demo_value: "all"`
- `inventory/group_vars/lab.yml` — `precedence_demo_value: "lab"`
- `playbooks/01_basics.yml` play vars — `precedence_demo_value: play`

Commands (from `automation/ansible`):

```powershell
# Expect: play (play vars beat group_vars)
..\python\.venv\Scripts\ansible-playbook.exe playbooks\01_basics.yml

# Expect: extra (CLI wins)
..\python\.venv\Scripts\ansible-playbook.exe playbooks\01_basics.yml -e precedence_demo_value=extra
```

Non-secret sample data for include_vars practice: `automation/ansible/vars/example_vars.yml`.

## Safety

Do not use precedence overrides to point Kubernetes or AWS playbooks at `platform-lab`, production VPCs, or shared ALBs. Keep overrides on disposable localhost markers and `automation-lab` only.
