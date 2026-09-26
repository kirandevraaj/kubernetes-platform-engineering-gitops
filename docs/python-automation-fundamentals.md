# Python Automation Fundamentals (Project 1)

**Status:** Section 24 teaching baseline — how Python becomes reliable platform automation in the Kubernetes Platform Engineering & GitOps Lab.

**Clusters:** VMware `ckad-lab` (Kubernetes 1.31.x) · AWS `platform-lab-aws` (EKS 1.36.x)  
**Safe mutation namespaces:** `automation-lab`, `security-lab`, `argo-advanced-lab`  
**Pinned client:** `kubernetes==32.0.1` · **App image (unchanged):** `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

Python is the **orchestration and logic** layer. It does not replace Terraform (infrastructure lifecycle), Ansible (multi-host desired configuration), Kubernetes manifests (workload desired state), Argo CD (continuous Git reconciliation), or Jenkins (CI/build/publish). It implements decisions, calls APIs, invokes Ansible Runner safely, and verifies outcomes.

---

## 1. Execution model

CPython reads source (`.py`), compiles to bytecode (`.pyc` / `__pycache__`), and executes on a virtual machine. Automation scripts are usually short-lived processes: start → load config → talk to APIs or subprocesses → exit with a code.

**Why it matters in Project 1:** every CLI (`platform-automate`, inventory helpers, doctors) is a process with an exit code that Jenkins and humans interpret. Success is `0`; validation failure, API denial, and wrong kube-context must be non-zero so pipelines fail closed.

Interactive REPL is for exploration only. Lab automation ships as modules under `automation/python/` invoked as `python -m …` or console scripts from a venv.

---

## 2. Imports, modules, and packages

| Concept | Meaning |
|---------|---------|
| **Module** | A single `.py` file (or C extension) loadable with `import` |
| **Package** | A directory of modules (historically with `__init__.py`) |
| **Absolute import** | `from platform_automate.k8s.client import load_api` — preferred |
| **Relative import** | `from .client import load_api` — only inside packages |

Keep API clients, domain logic, and CLI entrypoints in separate modules so tests can inject fakes (dependency injection). Business logic must not call `boto3.client(...)` or `kubernetes.config.load_kube_config()` deep inside nested helpers without an injectable boundary.

---

## 3. Virtual environments (`venv`)

A venv isolates site-packages from the system Python. On this workstation the lab uses **Python 3.14.6** under `automation/python/.venv`.

```text
cd automation/python
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows
pip install -r requirements.txt
```

**Why:** Ansible collections, `kubernetes`, `boto3`, `ruff`, and `mypy` must not pollute global Python. Reproducible CI and local doctor commands depend on the same pinned set recorded in [`docs/toolchain-inventory.md`](./toolchain-inventory.md).

---

## 4. `pip`, pinning, and lock discipline

- Pin **direct** dependencies with `==` in `requirements.txt` (e.g. `kubernetes==32.0.1`, `boto3==1.40.18`, `ansible-runner==2.4.1`).
- Prefer generating a lock or documenting transitive pins when CI must be bit-reproducible.
- Never `pip install` unpinned “latest” into the shared lab venv during demos.

**Pin rationale (`kubernetes==32.0.1`):** client major tracks Kubernetes OpenAPI adjacency around 1.32; Core/Apps APIs used by the lab (Namespace, Deployment, Service, Pod) work against both VMware 1.31.x and EKS 1.36.x. Do not bump casually — client/server skew can change watch/paging behavior.

---

## 5. Environment variables

Use env vars for **runtime secrets and context**, never commit them:

| Variable (examples) | Role |
|---------------------|------|
| `AWS_PROFILE` / `AWS_REGION` | Boto3 session selection |
| `KUBECONFIG` | Path to kubeconfig (prefer explicit context flags in CLI) |
| `PLATFORM_AUTOMATE_ENV` | `lab` vs forbidden production-like targets |
| `ANSIBLE_CONFIG` | Ansible cfg path under `automation/ansible/` |
| `LOG_LEVEL` | `INFO` default; `DEBUG` with `--verbose` |

Read with `os.environ.get("NAME", default)`. Fail fast if a required secret path is missing; never print secret values.

---

## 6. CLI arguments

Prefer `argparse` (stdlib) or a thin Typer/Click wrapper later. Project patterns:

- `--dry-run` — plan without mutate  
- `--confirm` — required for apply  
- `--context` — kube context (`ckad-lab` or AWS tools context)  
- `--timeout` / `--max-retries`  
- `--environment` — restrict to safe lab namespaces  

Reject `--force-all` style bypasses. Mutation of `platform-lab`, `storage-lab`, observability stacks, VPC, EKS, ALB, Jenkins architecture, or Argo global objects is **out of scope**.

---

## 7. Configuration files

Layer config by precedence (highest wins):

1. CLI flags  
2. Environment variables  
3. Local config file (YAML/JSON under `automation/python/config/`, gitignored secrets overlay)  
4. Built-in safe defaults (namespaces `automation-lab` only for mutate)

Validate schemas early (types, allowed namespaces, allowed contexts). Invalid config → exit `2` before any API call.

---

## 8. Logging

Use the stdlib `logging` module, not `print`, for automation:

- **DEBUG** — request IDs, retry attempts, inventory host lists  
- **INFO** — phase transitions (discover → plan → apply → verify)  
- **WARNING** — recoverable API throttling, soft drift  
- **ERROR** — failed verification, denied IAM/RBAC  
- **CRITICAL** — aborting run after partial failure policy trip  

Structured fields (`run_id`, `phase`, `resource`, `exit_code`) make Jenkins archives useful. Never log AWS keys, kube tokens, or Vault passwords.

---

## 9. Exceptions

Catch **narrow** exceptions near I/O boundaries; let unexpected bugs fail loudly in tests.

```text
API call
  → catch ClientError / ApiException / TimeoutExpired
  → map to domain error (AuthError, NotFound, Conflict, Throttled)
  → retry only if classified retryable
  → else log + non-zero exit
```

Avoid bare `except:` and swallowing errors in `finally` without re-raise. Use exception chaining (`raise X from e`) to preserve cause for runbooks.

---

## 10. Functions, classes, dataclasses, typing

- **Functions** for pure transforms (desired − actual → plan).  
- **Classes** for clients and controllers with injected dependencies (`PlatformController`).  
- **`@dataclass`** for Desired/Actual/Change/Risk records — immutable-ish data, clear fields.  
- **`typing`** (`Optional`, `Protocol`, `TypedDict`) so `mypy` catches wrong API shapes before a live cluster call.

Interview framing: classes hold *stateful adapters*; dataclasses hold *facts*; functions hold *rules*.

---

## 11. Generators

Generators (`yield`) stream large listings (pod lists, AWS paginator pages) without loading everything into memory. Prefer iterating boto3 paginators and Kubernetes list/continue tokens as generators in inventory and report phases.

---

## 12. Context managers

`with` ensures cleanup: temp kubeconfig copies, open files, locked workdirs, Runner private data dirs.

```python
with open(path, encoding="utf-8") as f:
    data = yaml.safe_load(f)
```

Custom context managers wrap “acquire API session → use → close” so exceptions still release handles.

---

## 13. JSON and YAML

| Format | Use in Project 1 |
|--------|------------------|
| **JSON** | Kubernetes API wire format, Jenkins archive reports, boto3 responses |
| **YAML** | Ansible playbooks/inventory, Kustomize overlays, human config |

Always `yaml.safe_load` / `json.loads` — never `yaml.load` with unsafe Loader. Round-trip reports as JSON for machines; YAML for humans.

---

## 14. Files and paths

Use `pathlib.Path` for all path joins. Resolve relative to repo root or package root, not the caller’s cwd, so Jenkins agents and Windows workstations behave the same.

Treat Git as authoritative for desired manifests; automation may **propose** Git commits for `automation-lab` only — never rewrite `kubernetes/overlays` image digests outside the Jenkins promotion path.

---

## 15. Subprocess automation

Use `subprocess.run([...], check=False, capture_output=True, text=True, timeout=...)` with an **argument list**, not a shell string.

| Rule | Why |
|------|-----|
| Prefer `shell=False` (default) | Avoid injection; quoting bugs |
| `shell=True` only if documented and inputs are constant | Rare: invoking `cmd.exe` builtins |
| Inspect `returncode` | Non-zero is not always “exception” — classify |
| Catch `TimeoutExpired` | Kill hung `ansible-playbook` / `terraform` |
| Never pass secrets on argv if avoidable | Prefer env or stdin |

Ansible Runner is preferred over raw `ansible-playbook` subprocess when Python must parse events; raw subprocess remains acceptable for doctor checks.

---

## 16. Exit codes

| Code | Meaning (lab convention) |
|------|----------------------------|
| `0` | Success / verify PASS |
| `1` | Generic runtime failure |
| `2` | Config / CLI validation error |
| `3` | Auth / RBAC / IAM denial |
| `4` | Verification FAIL |
| `5` | Partial failure (some hosts/resources OK) |
| `124` | Timeout (align with common CLI tools) |

Jenkins stages must fail on non-zero. Document codes in runbooks.

---

## 17. Signals

Handle `SIGINT` / `SIGTERM` (and Windows console break where applicable) to:

1. Stop scheduling new work  
2. Mark run as aborted in the report  
3. Exit non-zero without leaving silent half-applies unmarked  

Do not ignore signals during `apply`; prefer fail-visible over “finish at all costs.”

---

## 18. Timeouts

Every external call needs a budget:

- HTTP/API client timeouts (connect + read)  
- Subprocess `timeout=`  
- Overall CLI `--timeout` wall clock  

Timeouts are **safety**, not performance tuning. An EKS describe hanging behind a bad profile must not block Jenkins forever.

---

## 19. Retries

Retry only **transient** failures: throttling (`Throttling`, `429`), connection resets, `409` conflict on create-if-not-exists races, temporary API server unavailability.

Do not retry: bad credentials, 403 Forbidden, schema validation errors, wrong namespace policy denials.

Pattern: exponential backoff + jitter + max attempts (`--max-retries`). Log each attempt. After exhaustion, exit with a clear error for [`docs/runbooks/automation-failure.md`](./runbooks/automation-failure.md).

---

## Mental model checkpoint

| Layer | Tool | Python’s job |
|-------|------|--------------|
| Logic & orchestration | Python | Decide, sequence, verify |
| Multi-host config | Ansible (+ Runner) | Apply OS/network baselines when invoked |
| Cloud infra create | Terraform | Called only with explicit plan/apply boundaries |
| Workload desired state | Git manifests | Optionally commit lab-only changes |
| Continuous reconcile | Argo CD | Python must not `kubectl apply` production apps |
| CI | Jenkins | Test/lint/run automation — not live app deploy |

**Why Jenkins must not `kubectl apply` production app desired state:** that collapses CI and CD, bypasses Git history as the audit trail, races Argo CD self-heal, and makes rollback a Jenkins re-run instead of a Git revert. In Project 1, Jenkins builds `kirandevraaj/platform-lab`, publishes digest `sha256:1cca2b…`, and commits overlays; Argo CD syncs clusters.

---

## Related docs

- [Python platform automation](./automation/python-platform-automation.md)  
- [Automation architecture](./automation/automation-architecture.md)  
- [Master guide](./automation/platform-automation-master-guide.md)  
- [Toolchain inventory](./toolchain-inventory.md)  
