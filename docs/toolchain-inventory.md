# Toolchain Inventory (Project 1 — Section 24)

**Purpose:** Record discovered tools, versions, locations, and pin decisions for platform automation.  
**Policy:** Do not blindly upgrade. Prefer pins that keep VMware `ckad-lab` (1.31.x) and AWS EKS (1.36.x) automation reproducible.

**App image (unchanged this milestone):** `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## Inventory table

| tool | version | location | purpose |
|------|---------|----------|---------|
| Python | 3.14.6 | Windows Python install + `automation/python/.venv` | Automation runtime / orchestration |
| pip | bundled with 3.14.6 | `python -m pip` in venv | Install pinned Python deps |
| pytest | lab venv (installed with automation deps) | `automation/python/.venv` | Unit/contract tests |
| ruff | lab venv | `automation/python/.venv` | Lint/format Python |
| mypy | lab venv | `automation/python/.venv` | Optional static types |
| kubernetes (Python client) | **32.0.1** (pin) | venv site-packages | Python ↔ Kubernetes API |
| boto3 | **1.40.18** (pin) | venv site-packages | Python ↔ AWS APIs |
| botocore | transitive with boto3 1.40.18 | venv | AWS protocol/retries |
| ansible-runner | **2.4.1** (pin) | venv site-packages | Software invokes Ansible safely |
| ansible-core | **2.18.6** (pin) | venv / automation path (see notes) | Ansible language + builtins |
| ansible collections | amazon.aws `9.2.0`, kubernetes.core `5.1.0`, ansible.posix `1.6.2`, community.general `10.3.0` | `automation/ansible/collections` (via galaxy `-p collections`) | AWS/K8s/posix modules |
| kubectl | 1.36.1 | Windows client on PATH (typical lab) | Interactive / doctor Kubernetes CLI |
| helm | 4.2.3 | Windows client on PATH (typical lab) | Chart render/ops (observability etc.) |
| git | 2.54 | Windows Git | Source of truth VCS |
| aws CLI | **not on Windows PATH**; **not installed in WSL Ubuntu** (snapshot) | — | Human AWS CLI; automation prefers boto3 |
| terraform | **not on Windows PATH**; **not installed in WSL Ubuntu** (snapshot) | Expected under future install; code in `terraform/aws` | Infra lifecycle when installed |
| ansible (CLI on PATH) | **not reliably on Windows PATH** | Use venv / documented install | Playbook execution |
| WSL Ubuntu Python | 3.12 available | WSL | Optional experiments; **aws/terraform/ansible not installed there either** |
| Jenkins | Docker Desktop Compose lab | `jenkins/` on workstation | CI build/test/publish/promote; automation lint pipelines |
| Argo CD | VMware `v3.5.3` / AWS `v3.1.0` | In-cluster | GitOps reconcile |

---

## Pin decisions

| Pin | Decision | Rationale |
|-----|----------|-----------|
| `kubernetes==32.0.1` | **Required** | Client adjacency for VMware 1.31.x; Core/Apps API usage remains valid on EKS 1.36.x. Avoid casual major bumps (watch/paging skew). |
| `boto3==1.40.18` | **Required** | Stable Session/Client/paginator behavior for read-mostly lab automation. |
| `ansible-runner==2.4.1` | **Required** | Structured events and timeouts vs brittle subprocess scraping. |
| ansible-core `2.18.6` | **Required** | Match collection compatibility; reproducible play semantics. |
| Collections (see `automation/ansible/collections/requirements.yml`) | **Required** | amazon.aws / kubernetes.core versions locked for lint + module surface. |
| kubectl 1.36.1 | **Accept discovered** | Client skew vs 1.31 server is normal; use for doctor, not as API source of truth. |
| helm 4.2.3 / git 2.54 | **Accept discovered** | Platform tooling already in use. |
| Python 3.14.6 | **Accept discovered Windows runtime** | Lab venv standard; document if CI uses different minor. |
| aws CLI / terraform / ansible on PATH | **Document absence** | Do not block docs; install when executing live infra/playbooks; prefer boto3 + Runner from venv where possible. |

---

## Safety reminders

- No secrets in this file or in Git.  
- Do not mutate `platform-lab` / storage / observability / VPC / EKS / ALB via casual CLI.  
- Jenkins must not `kubectl apply` production app desired state—Git + Argo CD remain the deploy path.

---

## Related

- [python-automation-fundamentals.md](./python-automation-fundamentals.md)  
- [automation/platform-automation-cheat-sheet.md](./automation/platform-automation-cheat-sheet.md)  
- [automation/automation-command-reference.md](./automation/automation-command-reference.md)  
