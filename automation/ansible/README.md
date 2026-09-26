# Ansible learning tree — Section 24

Production-grade **learning** layout for the Kubernetes Platform Engineering & GitOps Lab.  
Mutations stay on **localhost** disposable paths or namespace **`automation-lab`**. Do not target `platform-lab`, `storage-lab`, observability, VPC, EKS, ALB, Jenkins, or Argo global.

## Prerequisites

1. Project venv under `automation/python/.venv` (create if needed).
2. Prefer a **Linux / WSL Ansible controller**. Native Windows may fail ansible CLI startup (`fcntl` / blocking IO).
3. Install Ansible + AWS/K8s Python deps into that venv, for example:

```powershell
cd "..\python"
.\.venv\Scripts\python.exe -m pip install "ansible-core>=2.16,<2.19" boto3 botocore kubernetes
cd "..\ansible"
..\python\.venv\Scripts\ansible-galaxy.exe collection install -r collections\requirements.yml -p collections
```

**Collections are not part of ansible-core.** They are installed separately via `ansible-galaxy` from `collections/requirements.yml` (`amazon.aws`, `kubernetes.core`, `ansible.posix`, `community.general`).

## How to run (Windows)

From `automation/ansible`:

```powershell
..\python\.venv\Scripts\ansible-playbook.exe playbooks\01_basics.yml
..\python\.venv\Scripts\ansible-playbook.exe playbooks\06_idempotency.yml
```

Or activate the venv, then use `ansible-playbook` on PATH:

```powershell
..\python\.venv\Scripts\Activate.ps1
ansible-playbook playbooks\01_basics.yml
```

## How to run (Unix / activated venv)

```bash
source ../python/.venv/bin/activate   # or your venv path
ansible-playbook playbooks/01_basics.yml
```

## Playbook map

| Playbook | Topic | Safety |
|---|---|---|
| `01_basics.yml` | Facts, FQCN, precedence | localhost |
| `02_packages.yml` | Modules / pip venv | disposable workdir |
| `03_files.yml` | file/copy/lineinfile | disposable workdir |
| `04_templates.yml` | Jinja template | disposable workdir |
| `05_services.yml` | Service concept + handlers | simulated locally |
| `06_idempotency.yml` | Second run `changed=0` | modules only |
| `07_handlers.yml` | Notify only on change | localhost |
| `08_loops.yml` | loop / dict2items | localhost |
| `09_error_handling.yml` | block/rescue/always | controlled fail |
| `10_delegation.yml` | delegate_to + optional ping | workers read-only |
| `11_kubernetes_lab.yml` | `kubernetes.core.k8s` | **automation-lab only** |
| `12_aws_readonly.yml` | EC2/VPC info | read-only |
| `13_aws_safe_tag.yml` | Optional tag | `--check` / opt-in |
| `14_vault_example.yml` | Vault FAKE secrets | no real creds |
| `15_platform_baseline.yml` | Roles | localhost markers |

## Inventory

- `inventory/hosts.yml` — `localhost` + optional VMware workers (commented; read-only).
- `inventory/aws_ec2.yml` — `amazon.aws.aws_ec2` dynamic inventory by tags. **Static AWS IP lists are fragile**; prefer this plugin.

```powershell
..\python\.venv\Scripts\ansible-inventory.exe -i inventory\aws_ec2.yml --graph
```

## Vault (FAKE secrets)

See `vars/vault_example.yml.enc_instructions.md`. Lab password for the exercise: `lab-vault-password`.

```powershell
Set-Content -NoNewline -Path .vault_pass_lab.txt -Value "lab-vault-password"
..\python\.venv\Scripts\ansible-vault.exe encrypt vars\vault_example_plaintext.yml --vault-password-file .vault_pass_lab.txt --output vars\vault_example.yml
..\python\.venv\Scripts\ansible-playbook.exe playbooks\14_vault_example.yml --vault-password-file .vault_pass_lab.txt
```

Do **not** commit `.vault_pass_lab.txt` or real credentials.

## Variable precedence

Comments in `playbooks/01_basics.yml` plus repo doc [`docs/ansible-variable-precedence.md`](../../docs/ansible-variable-precedence.md).

Quick check:

```powershell
..\python\.venv\Scripts\ansible-playbook.exe playbooks\01_basics.yml -e precedence_demo_value=extra
```

## Roles

- `platform_common` — baseline markers  
- `platform_service` — simulated service config  
- `platform_node` — read-only facts (optional for workers)

Each role documents interface / outputs / idempotency in its `README.md`.

## ansible.cfg highlights

- `inventory = inventory`
- `roles_path = roles`
- `collections_paths = collections:~/.ansible/collections`
- `host_key_checking = False` (lab)
- `retry_files_enabled = False`
- `stdout_callback = default`

Use **FQCN** everywhere (already applied in playbooks/roles).
