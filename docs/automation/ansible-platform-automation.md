# Ansible Platform Automation (Project 1)

**Status:** Section 24 — Ansible as declarative multi-system configuration, invoked safely from Python.

**Inventory home:** `automation/ansible/inventory/` · **Collections:** `automation/ansible/collections/requirements.yml`  
**Pinned:** ansible-core **2.18.6**, ansible-runner **2.4.1**, collections amazon.aws `9.2.0`, kubernetes.core `5.1.0`, ansible.posix `1.6.2`, community.general `10.3.0`

**Safety:** Prefer `localhost` for mutations. VMware workers are **read-only** (ping/setup). Do not install packages or rewrite configs on `ckad-lab` nodes. Do not mutate `platform-lab` workloads.

Ansible is **not** a replacement for Terraform, Argo CD, or Jenkins. It configures and validates many systems idempotently when Python (or a human) decides a playbook should run.

---

## Architecture

```text
Control node (workstation / CI agent)
    |  inventory (static YAML + optional aws_ec2)
    |  playbooks / roles / collections
    v
Modules (FQCN) ----SSH/local----> Managed nodes (or localhost / API proxies)
```

Python may sit **above** this stack via Ansible Runner: decide *whether* and *with which extra vars*, then parse events and verify outside Ansible.

---

## Control node

Where `ansible` / `ansible-playbook` execute. In Project 1 this is the Windows lab venv/agent path (note: ansible may not be on Windows PATH — install/use via venv or documented WSL once available). The control node holds inventory, roles, Vault passwords (env only), and collection installs under `./collections`.

---

## Inventory

Static inventory: `automation/ansible/inventory/hosts.yml`

- Group `lab` → `localhost` with `ansible_connection: local` for safe mutation drills  
- Group `vmware_workers` → optional read-only hosts (`lab_readonly: true`)  
- AWS: **do not** hardcode public IPs; use `amazon.aws.aws_ec2` dynamic inventory keyed by tags  

Inventory answers *who*; playbooks answer *what*.

---

## Managed nodes

Targets that modules act on: local Python interpreter, SSH Linux VMs, or cloud/API endpoints via collections. Treat VMware Kubernetes nodes as **production-like lab infrastructure** — configuration drift experiments belong on disposable localhost or dedicated automation VMs, not worker OS mutation.

---

## Ad-hoc

```bash
ansible lab -i inventory/hosts.yml -m ansible.builtin.ping
ansible lab -i inventory/hosts.yml -m ansible.builtin.setup
```

Ad-hoc is for discovery and doctor checks. Persistent desired state lives in playbooks/roles.

---

## Playbooks

YAML documents listing plays: hosts, gather_facts, tasks, handlers, vars. Capstone uses bounded plays (e.g. prepare lab baseline on localhost, validate node facts) — not “automate the entire platform.”

---

## Tasks

Ordered module invocations. Each task should be idempotent: running twice yields `ok` / `changed=0` when already converged. Name tasks clearly for Runner event logs and Jenkins archives.

---

## Modules

Units of work (`ansible.builtin.copy`, `kubernetes.core.k8s`, `amazon.aws.ec2_instance_info`, …). Prefer **FQCN** (fully qualified collection name) so resolution does not depend on ambiguous short names.

---

## Facts

`setup` / gathered facts describe actual state (OS, memory, IPs). Use facts in conditionals; do not invent host reality in vars. For API-only targets, facts may be minimal — rely on module return data instead.

---

## Variables

Sources: inventory, group_vars, host_vars, play vars, `extra_vars` (`-e` / Runner), registered results. Keep secrets in Vault or CI credentials — never plaintext in Git.

---

## Precedence

Ansible’s precedence chain is a frequent interview topic. Remember the operational rule for Project 1: **CLI `extra_vars` from Python win** for run-scoped values (namespace, dry_run, confirm token metadata), while inventory group vars hold stable lab defaults. Do not fight precedence with duplicate definitions in five places.

---

## Templates

Jinja2 templates (`template` module) render config files from vars. Use for lab service configs on localhost — not for rewriting Argo-managed Kubernetes manifests that belong in Git.

---

## Loops

`loop` / `with_*` for repetitive identical tasks (ensure list of packages, ensure list of directories). Prefer clear loops over copy-paste tasks. Limit fan-out against AWS APIs to avoid throttling.

---

## Conditionals

`when:` gates tasks on facts or prior registers. Use to skip VMware worker mutation when `lab_readonly` is true — defense in depth beyond inventory comments.

---

## Handlers

Handlers run once at end (or flushed) when notified — classic “restart only if config changed.” They preserve idempotency: unchanged config → no restart.

---

## Roles

Reusable directories (`tasks/`, `handlers/`, `templates/`, `defaults/`, `meta/`). Project 1 roles should be small: `lab_baseline`, `lab_validate`, not a mega-role that creates EKS.

---

## Collections

Versioned bundles of modules/plugins/roles. Install with:

```bash
ansible-galaxy collection install -r collections/requirements.yml -p collections
```

Pins in `requirements.yml` keep amazon.aws / kubernetes.core stable across machines.

---

## FQCN

Fully qualified collection names (`ansible.builtin.file`, `kubernetes.core.k8s`) avoid collisions and make lint rules happier. Require FQCN in ansible-lint config for the lab.

---

## Check mode

`ansible-playbook --check` predicts changes without applying (module-dependent). Python plan phase should prefer check mode or native dry-run before `--confirm` apply.

---

## Diff mode

`--diff` shows before/after for supporting modules. Use in CI dry-run archives so reviewers see intent.

---

## Idempotency

Desired declarative modules converge actual → desired. Signal `changed` only when mutation occurred. Non-idempotent `command`/`shell` must be justified, guarded with `creates`/`removes`/`changed_when`, or avoided.

---

## Error handling

`block` / `rescue` / `always`, `ignore_errors` (rare), `failed_when`, `any_errors_fatal`, `max_fail_percentage`. For Project 1: fail the play on unexpected mutation errors; map Runner failure to Python verify FAIL.

---

## Delegation

`delegate_to:` runs a task on another host (e.g. API call from localhost while looping inventory). Useful for “check AWS from control node while iterating tags.” Do not delegate destructive tasks to VMware workers.

---

## Dynamic inventory

`amazon.aws.aws_ec2` builds host lists from AWS APIs filtered by tags. Static IP lists break when instances stop/start. Dynamic inventory is the bridge from Ansible to AWS truth — still read-mostly for this lab unless tagged safely.

---

## AWS

Use collections for describe/info modules first. Creating VPC/EKS/ALB remains **Terraform** under `terraform/aws`. Ansible may validate tags or gather facts; it must not become a shadow Terraform.

---

## Kubernetes

`kubernetes.core` can apply YAML declaratively. In Project 1, Ansible Kubernetes usage is limited to **lab namespaces** and teaching idempotent apply. Production-like apps stay Git → Argo CD. Prefer Python client for complex orchestration; Ansible for declarative “ensure these lab objects exist.”

---

## Vault

`ansible-vault` encrypts secret vars at rest. Unlock via CI credential or local env — never commit vault passwords. Prefer external secret stores conceptually; Vault is the lab mechanism for encrypted group_vars.

---

## Linting

`ansible-lint` catches risky modules, missing FQCN, and anti-patterns. Jenkins runs lint before dry-run. Treat lint failures as merge blockers for automation PRs.

---

## Testing

- Syntax: `ansible-playbook --syntax-check`  
- Molecule optional later  
- Pytest can assert Runner exit codes with mocked private data dirs  
- Integration: localhost plays only by default  

---

## CI/CD

Jenkins automation pipeline stages: checkout → Python tests → ruff → ansible-lint → check/diff dry-run → plan → optional confirmed lab apply → verify → archive.

Jenkins still **does not** kubectl-apply `platform-lab`. If Ansible/Python changes Git desired state for `automation-lab`, Argo CD reconciles — same GitOps boundary as app digests.

---

## Python orchestration pattern

```text
Python PlatformController
  → Ansible Runner (playbook, inventory, extravars, timeouts)
  → events (ok/changed/failed/unreachable)
  → Python verification (K8s API / boto3 / local asserts)
  → report + exit code
```

**Why Runner:** structured events, isolation of private data dirs, safer than brittle stdout scraping, timeouts and cancelation hooks.

---

## Related

- [Python platform automation](./python-platform-automation.md)  
- [Automation architecture](./automation-architecture.md)  
- [VMware/NSX bridge](./vmware-nsx-automation-bridge.md)  
- [Ansible failure runbook](../runbooks/ansible-failure.md)  
