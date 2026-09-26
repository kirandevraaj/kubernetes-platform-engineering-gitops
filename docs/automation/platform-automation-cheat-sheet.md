# Platform Automation Cheat Sheet (Project 1)

Quick reference for Section 24. Details: [master guide](./platform-automation-master-guide.md) · [command reference](./automation-command-reference.md)

**Safe mutate NS:** `automation-lab` · **Contexts:** `ckad-lab`, AWS tools · **Image pin:** `0.1.4` / `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## Python

| | |
|--|--|
| **Purpose** | Orchestration logic, API clients, verification, reports |
| **Home** | `automation/python/.venv` (Python 3.14.6) |
| **Pins** | `kubernetes==32.0.1`, `boto3==1.40.18`, `ansible-runner==2.4.1` |
| **Patterns** | DI adapters · dataclasses Desired/Actual/Plan · `--dry-run` / `--confirm` · exit codes |
| **Failures** | Wrong context · unpinned deps · swallowed exceptions · `shell=True` injection · hanging without timeout |

```text
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
ruff check .
mypy platform_automate
```

---

## Boto3

| | |
|--|--|
| **Purpose** | Python ↔ AWS APIs |
| **Patterns** | `Session` → client → paginator · classify `ClientError` · read-mostly inventory |
| **Failures** | Wrong profile/region · AccessDenied · missing pagination · mutating Terraform-owned VPC/EKS |

```text
# Conceptual
session = boto3.Session(profile_name=..., region_name=...)
eks = session.client("eks")
```

---

## Kubernetes Python client

| | |
|--|--|
| **Purpose** | Python ↔ Kubernetes API (not a kubectl wrapper) |
| **Pin** | `32.0.1` (VMware 1.31 adjacency; Core/Apps OK on EKS 1.36) |
| **Patterns** | load kubeconfig context · get/create/patch in `automation-lab` · wait Ready |
| **Failures** | 403 RBAC · wrong namespace · fighting Argo on `platform-lab` · no timeout on watch |

---

## Ansible

| | |
|--|--|
| **Purpose** | Declarative multi-host configuration |
| **Pins** | ansible-core 2.18.6 · collections in `automation/ansible/collections/requirements.yml` |
| **Patterns** | inventory · roles · FQCN · check/diff · Vault · `lab_readonly` on workers |
| **Failures** | Mutating VMware workers · short module names · secrets in Git · ignoring failed hosts |

```text
ansible-galaxy collection install -r collections/requirements.yml -p collections
ansible-playbook -i inventory/hosts.yml playbooks/lab_validate.yml --check --diff
ansible-lint
```

---

## Terraform

| | |
|--|--|
| **Purpose** | Declarative AWS infrastructure lifecycle (`terraform/aws`) |
| **Patterns** | plan → review → apply · remote state · IAM least privilege |
| **Failures** | Shadow-managing VPC with boto3/Ansible · editing state by hand · ungated destroy |

**Note:** `terraform` may be absent from Windows PATH / WSL in this workstation snapshot—install before live applies; docs still define the boundary.

---

## Jenkins

| | |
|--|--|
| **Purpose** | CI: test, build, publish image, promote digest commits; run automation lint/dry-run |
| **Patterns** | `app/**` gate · dual overlay digest promote · credentials in Jenkins store |
| **Failures** | Adding `kubectl apply` for apps · leaking secrets in logs · concurrent promotions |

**Never:** Jenkins kubectl-applies production app desired state (ADR-006 / GitOps boundary).

---

## Argo CD

| | |
|--|--|
| **Purpose** | Continuously reconcile Git → cluster (VMware v3.5.3 / AWS v3.1.0) |
| **Patterns** | Applications · AppProjects · prune/self-heal · sync options |
| **Failures** | Live drift fighting self-heal · weak AppProject wildcards · Force/Replace on prod apps |

---

## Git

| | |
|--|--|
| **Purpose** | Authoritative desired state (manifests, Terraform, Argo objects, automation code) |
| **Patterns** | Digest promotion commits · revert for rollback · PR review |
| **Failures** | Secrets committed · bypassing Git with live-only fixes |

---

## Decision crumbs

```text
Logic? Python | Many hosts config? Ansible | Infra create? Terraform
K8s desired? Git manifests | Reconcile? Argo | CI artifacts? Jenkins
AWS API? Boto3 | K8s API? kubernetes client | Invoke Ansible? Runner
```

---

## Related

- [architecture](./automation-architecture.md) · [interview notes](../automation-interview-notes.md) · [toolchain](../toolchain-inventory.md)
