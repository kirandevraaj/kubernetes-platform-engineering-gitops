# Python Platform Automation (Project 1)

**Status:** Section 24 — full teaching guide for Python as the platform automation runtime.

**Scope:** Orchestration logic, Kubernetes Python client, Boto3, Ansible Runner, testing, and observability.  
**Safe targets only:** namespaces `automation-lab`, `security-lab`, `argo-advanced-lab`. Do not mutate `platform-lab`, `storage-lab`, observability, VPC, EKS topology, ALB, Jenkins architecture, or Argo CD global configuration.

**Pinned:** `kubernetes==32.0.1`, `boto3==1.40.18`, `ansible-runner==2.4.1` · **App image unchanged:** `0.1.4` / `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## Python runtime

Project 1 automation runs on **CPython 3.14.6** in a dedicated venv under `automation/python/.venv`. The runtime is a short-lived process: load config → discover → validate → plan → (optional) apply → verify → report → exit.

WSL Ubuntu may expose Python 3.12 for experiments, but aws CLI / terraform / ansible are **not** assumed installed there either. Treat the Windows venv as the documented automation home; see [`docs/toolchain-inventory.md`](../toolchain-inventory.md).

Why a fixed runtime matters: Kubernetes client codegen, Ansible collections, and boto3 paginator behavior all drift with unpinned upgrades. Lab demos and interview answers assume this pin set.

---

## Project structure

Recommended layout (logic separated from adapters):

```text
automation/python/
  platform_automate/          # importable package
    cli.py                    # argparse entry
    config.py                 # load + validate
    controller.py             # PlatformController
    adapters/
      kubernetes_api.py
      aws_boto3.py
      ansible_runner_adapter.py
      terraform_cli.py         # boundary only; rarely mutate
    models/                   # dataclasses: Desired, Actual, Plan
    report.py
  tests/
  config/                     # non-secret defaults
  requirements.txt
  .venv/
```

**Rule:** domain code depends on Protocols/interfaces; adapters construct real clients. That enables unit tests without live EKS or VMware.

---

## Virtual environments

Always activate the lab venv before doctor/inventory/reconcile. Never install lab pins into the system Python. Document `python -m venv` recreation steps in the cheat sheet so a clean machine matches CI.

---

## Dependency management

`requirements.txt` pins direct deps. Regenerate only in a reviewed change with changelog notes. Key pins:

| Package | Version | Why |
|---------|---------|-----|
| kubernetes | 32.0.1 | Adjacent to VMware 1.31; Core/Apps OK on EKS 1.36 |
| boto3 | 1.40.18 | Stable Session/Client APIs for read-mostly lab |
| ansible-runner | 2.4.1 | Structured events vs raw subprocess |
| pytest / ruff / mypy | lab-installed | Test, lint, types |

Ansible-core `2.18.6` and collections live under `automation/ansible/` (see Ansible doc). Python depends on Runner to invoke them safely.

---

## CLI

Expose a single console narrative:

```text
platform-automate doctor
platform-automate inventory
platform-automate validate
platform-automate plan
platform-automate reconcile --confirm
platform-automate verify
platform-automate report
```

Operability flags: `--verbose`, `--quiet`, `--dry-run`, `--confirm`, `--timeout`, `--max-retries`, `--environment`, `--context`.

Mutations require `--confirm`. There is no `--force-all`. Wrong context or forbidden namespace → exit before API writes.

---

## Configuration

Config answers: which kube context, which AWS profile/region, which Ansible inventory, which safe namespace, timeout budgets. Precedence: CLI > env > file > defaults.

Validate allow-lists:

- Contexts: `ckad-lab`, AWS tools context (e.g. via `platform-aws-tools`)  
- Namespaces for mutate: `automation-lab` (primary), optionally documented lab-only sets  
- Deny: `platform-lab`, `kube-system`, `argocd` (except read), etc.

---

## Logging

One logger hierarchy (`platform_automate.*`). JSON-lines optional for Jenkins archives; human text for interactive runs. Correlate with `run_id`. Never log secrets. Map log level to `--verbose` / `--quiet`.

---

## Exceptions

Translate library exceptions at adapter edges:

| Source | Examples | Domain mapping |
|--------|----------|----------------|
| kubernetes | `ApiException` 401/403/404/409/429 | Auth, Forbidden, NotFound, Conflict, Throttled |
| boto3 | `ClientError` codes | same taxonomy + IAM |
| subprocess | `TimeoutExpired`, non-zero | Timeout, ToolFailed |
| ansible-runner | failed events | PlayFailed, Unreachable |

Controller code catches domain errors, not raw SDK types.

---

## Subprocess

Use argument vectors; capture stdout/stderr; enforce timeout; classify return codes. Prefer Ansible Runner for playbooks. Terraform/kubectl subprocesses are **diagnostic or plan-only** unless a documented lab exception applies — app deploy remains Git → Argo CD.

---

## REST

Generic REST (e.g. mock NSX Manager) uses `urllib` or `httpx`/`requests` with:

- Base URL from config  
- Token from env (never Git)  
- Timeouts, retries on 429/5xx  
- JSON encode/decode  
- Idempotent verbs where the API allows  

Same mental model as Kubernetes/AWS: discover → desired → apply → verify.

---

## Kubernetes client

`kubernetes` Python package talks to the API server the same way `kubectl` does (REST + auth plugins), without shelling out.

**Auth:** `load_kube_config(context=...)` on the workstation; in-cluster config only if a future controller pod is introduced (not required for Section 24 docs).

**Safe operations:** list/get namespaces, deployments, pods in `automation-lab`; create/update lab-only resources with idempotent create-or-patch.

**Forbidden:** patching `platform-lab` Deployment image, deleting storage PVCs, changing Argo Application specs for production apps.

**Why client over kubectl subprocess:** structured errors, watches, no shell quoting, easier mocking, explicit RBAC via kubeconfig user.

Pin `32.0.1` so list/watch/patch semantics stay stable across `ckad-lab` 1.31.x and EKS 1.36.x for Core/Apps.

---

## Boto3

Boto3 is Python ↔ AWS APIs. Prefer **read** for inventory (EKS describe, EC2 describe with tags, VPC describe) using profile/region from env.

**Sessions** centralize credentials. **Clients** map 1:1 to service APIs. **Resources** are higher-level sugar — use clients when you need paginators and explicit error codes.

**Safe mutation** (if any): only resources tagged for `automation-lab` / explicit lab project tags — never Terraform-managed VPC/EKS/ALB. Prefer dry-run flags where AWS supports them.

**Why Boto3 over aws CLI subprocess:** pagination helpers, typed errors, retry config, test doubles.

---

## Testing

Pyramid:

1. **Unit** — pure plan logic, dataclass transforms, retry classifiers (pytest)  
2. **Adapter contract** — mock `ApiException` / `ClientError`  
3. **Integration (opt-in)** — real `ckad-lab` read-only doctor against `automation-lab`  

Jenkins automation pipeline: unit → ruff → ansible-lint → dry-run → plan → (lab) apply → verify → archive reports. No secrets in logs or artifacts.

---

## Retries

Retry transient AWS throttles, API server blips, and conflict races. Exponential backoff + jitter. Cap with `--max-retries`. Record attempts in the report for interview storytelling and runbook evidence.

---

## Timeouts

Per-call and global wall-clock timeouts. Ansible Runner jobs inherit the CLI timeout. Hung verify must not leave Jenkins blue forever — fail with code `124` or domain Timeout.

---

## Concurrency

Use concurrency for **independent reads** (fan-out inventory across namespaces or accounts). Serialize mutations that share state. Thread pools are enough for sync SDK clients; document that Ansible parallel forks are a separate dial (`forks` / strategy).

Compare sequential vs concurrent in performance labs: measure runtime, request count, failure rate — concurrency amplifies rate-limit pain.

---

## Security

- No secrets in Git  
- Least-privilege kube RBAC ServiceAccount for any in-cluster future agent  
- Least-privilege IAM for automation profile (read-mostly + tagged mutate)  
- Refuse unexpected contexts/namespaces  
- `--confirm` gate  
- Do not disable TLS verify except documented local mock servers  

---

## Observability

Every run emits:

- Phase timeline  
- Desired vs actual summary  
- Changes applied / skipped  
- Verify PASS|FAIL|UNKNOWN  
- Exit code  

Archive JSON reports in Jenkins. Optional: emit metrics counters later; logs + reports are the Section 24 baseline. Tie failures to runbooks under `docs/runbooks/`.

---

## Boundary reminder (interview “why”)

| Need | Use | Not Python alone |
|------|-----|------------------|
| Complex branching / multi-API orchestration | Python | — |
| Configure many OS hosts the same way | Ansible via Runner | Hand-rolled SSH loops |
| Create VPC/EKS | Terraform | Boto3 “create everything” scripts |
| App desired state continuously | Git + Argo CD | Jenkins `kubectl apply` |
| Build/publish image digest | Jenkins | Argo CD |

Jenkins **must not** kubectl-apply production app desired state: it would bypass Git as source of truth, fight Argo self-heal on `platform-lab-local` / `platform-lab-aws`, and erase the digest promotion audit trail (`0.1.4` / `sha256:1cca2b…`).

---

## Related

- [Python fundamentals](../python-automation-fundamentals.md)  
- [Ansible platform automation](./ansible-platform-automation.md)  
- [Automation architecture](./automation-architecture.md)  
- [Master guide](./platform-automation-master-guide.md)  
