# Automation Interview Notes (Project 1)

Concise answers grounded in the **Kubernetes Platform Engineering & GitOps Lab**: VMware `ckad-lab` (1.31.x), AWS EKS `platform-lab-aws` (1.36.x), Jenkins CI, Argo CD (VMware v3.5.3 / AWS v3.1.0), Terraform under `terraform/aws`, automation under `automation/`. App image remains `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`. Safe mutate namespaces: `automation-lab`, `security-lab`, `argo-advanced-lab`.

---

## 1. Why Python for infrastructure automation?

Python is the **logic and orchestration** language: branching, retries, multi-API workflows, reports, and testable controllers (`PlatformController`). In Project 1 it talks to AWS via boto3, Kubernetes via `kubernetes==32.0.1`, and Ansible via Ansible Runner—without replacing Terraform, Argo CD, or Jenkins.

## 2. Why Ansible?

Ansible **declaratively configures many systems** with idempotent modules, inventory, roles, check/diff, and Vault. Project 1 uses it for bounded ops (localhost baseline/validate, read-only VMware facts)—not to create EKS or deploy `platform-lab`.

## 3. Python vs Ansible?

Python = complex decisions and multi-service orchestration. Ansible = convergent multi-host configuration. Pattern: **Python decides → Ansible Runner executes → Python verifies**. Do not rewrite Ansible in Python SSH loops, and do not force Ansible into every API workflow.

## 4. Boto3 vs AWS CLI?

Boto3 embeds AWS calls in code with paginators, structured `ClientError`, retries, and mocks. AWS CLI is fine for humans/doctor shells. Project automation prefers boto3 (`1.40.18`); CLI may be missing from PATH on this workstation anyway.

## 5. Kubernetes Python client vs kubectl?

Both speak the API. The client gives typed calls, watches, errors, and test doubles without shell quoting. kubectl remains for interactive ops. Lab pin `kubernetes==32.0.1` covers Core/Apps on 1.31 and 1.36. Neither should bypass GitOps for `platform-lab`.

## 6. Why idempotency?

Retries and re-runs must not duplicate resources or flip-flop state. Ansible `changed=false`, Terraform no-op plans, and K8s create-or-patch embody this. Non-idempotent shell is a last resort.

## 7. What is variable precedence?

Ansible’s ordered sources of vars; **extra_vars** (often from Python) win for a run. Inventory/group defaults hold stable lab values. Duplicate conflicting defs are a design smell.

## 8. What are handlers?

Tasks that run on **notify** when something changed—e.g., restart once after template update—preserving idempotent service management.

## 9. What are roles?

Reusable directory packages (`tasks`, `handlers`, `templates`, `defaults`). Project 1 keeps roles small (`lab_baseline`, `lab_validate`), not mega-platform roles.

## 10. What are collections?

Versioned bundles of modules/plugins/roles. Installed from `automation/ansible/collections/requirements.yml` (amazon.aws, kubernetes.core, …). `ansible-core` alone is insufficient for AWS/K8s modules.

## 11. Why FQCN?

Fully qualified names (`ansible.builtin.copy`) avoid collisions and satisfy ansible-lint—required lab style.

## 12. What is dynamic inventory?

Inventory built from APIs (e.g., `amazon.aws.aws_ec2` by tags) instead of brittle static public IPs that break across stop/start.

## 13. What is check mode?

`ansible-playbook --check` predicts changes without applying (module-dependent). Used in CI dry-run and Python plan phases before `--confirm`.

## 14. What is diff mode?

`--diff` shows before/after for supporting modules—archived in Jenkins for review.

## 15. What is Ansible Vault?

Encryption for secret vars at rest. Unlock via CI/env—**never** commit vault passwords or plaintext cloud keys in Git.

## 16. How does Ansible handle failure?

Failed tasks abort the play unless `block/rescue`, `ignore_errors`, or failure percentage settings intervene. Project 1 prefers fail-visible; Runner maps failure to Python verify FAIL / non-zero exit.

## 17. What is delegation?

`delegate_to` runs a task on another host (often localhost API calls while looping inventory). Do not delegate OS mutation onto `ckad-lab` workers.

## 18. What is Ansible Runner?

Library/CLI that lets **software invoke Ansible safely** with private data dirs and structured events (`ok`/`changed`/`failed`). Pin `ansible-runner==2.4.1`—preferred over scraping `ansible-playbook` stdout.

## 19. Where does Terraform fit?

**Declarative infrastructure lifecycle** for AWS (`terraform/aws`: VPC, EKS, IAM, LB controller, Argo bootstrap). Not for app image digests or day-2 OS config.

## 20. Where does Jenkins fit?

**CI**: test, build, publish `kirandevraaj/platform-lab`, promote digest to overlays; also lint/dry-run automation. **Not** CD via kubectl to clusters (ADR-006).

## 21. Where does Argo CD fit?

**CD / continuous reconciliation** of Git desired state to VMware and EKS (separate instances). Prune, self-heal, sync options—builds nothing.

## 22. How do you prevent direct Jenkins-to-Kubernetes deployment?

Policy + pipeline design: no kubectl/argo deploy steps for apps; only digest Git commits; Argo syncs; code review/ADR-006; AppProject boundaries. Automation pipelines may touch `automation-lab` only with confirm gates—not `platform-lab`.

## 23. How do you design safe automation?

Allow-listed contexts/namespaces, `--dry-run`/`--confirm`, least privilege IAM/RBAC, timeouts/retries, no `--force-all`, lint/tests, refuse mutating Terraform-owned infra via scripts, GitOps for app desired state.

## 24. How do you test infrastructure automation?

Unit-test plan/diff; mock SDK errors; ansible-lint + check/diff; optional live read-only doctor; failure injection (wrong context, AccessDenied, timeouts). Jenkins archives reports.

## 25. How do you handle API rate limiting?

Backoff/jitter, lower forks/concurrency, paginate politely, short-term cache inventory, classify 429 as retryable, budget total runtime.

## 26. How do you implement retries?

Retry transient faults only (throttle, timeout, conflict); cap with `--max-retries`; exponential backoff; never retry 401/403/validation; log attempts.

## 27. How do you prevent duplicate resource creation?

Natural keys + get-before-create; idempotent modules; Terraform state; Kubernetes create-or-patch; treat 409 as refresh/retry, not blind recreate.

## 28. How do you detect drift?

Compare desired vs actual (Python plan, Ansible check, `terraform plan`, Argo OutOfSync). Self-heal restores Git-owned apps; ops drift on lab objects is reconciled by `platform-automate`.

## 29. What is eventual consistency?

APIs may acknowledge before all readers see final state. Always verify (pod Ready, AWS describe, NSX realization) with timeouts → PASS/FAIL/UNKNOWN.

## 30. How would you automate VMware/NSX?

Same loop on Manager REST (mock OK): discover inventory/TN/Edge/segments/DFW → desired YAML → idempotent apply → verify realization → serial upgrade waves with rollback. See `vmware-nsx-automation-bridge.md`. Do not conflate with Calico/GitOps NetworkPolicy on `ckad-lab`.

## 31. How would you automate an EKS platform?

Terraform creates cluster/VPC/IAM; boto3 reads/describes; kubeconfig + Python/Argo manage workloads; Jenkins promotes digests; Ansible optional for node baseline if separated from Terraform. Never recreate EKS from ad-hoc boto3 in this lab.

## 32. How would you handle partial failure?

Per-target results, exit code `5`, stop further waves, mark unfinished work, optional compensating rollback, human-readable report—never claim global SUCCESS.

## 33. How do you protect credentials?

Jenkins credential store, env vars, Vault, IAM roles, short-lived tokens; never Git; redact logs; least privilege profiles/ServiceAccounts.

## 34. How do you design rollback?

Prefer reverse plan / previous desired snapshot; for GitOps apps `git revert` + Argo sync; avoid blind destroy; record pre-change evidence.

## 35. What should never be automated blindly?

Ungated production destroys; firewall “delete all”; Force/Replace on StatefulSets; Jenkins kubectl deploy of apps; mutating VPC/EKS/ALB outside Terraform; disabling TLS verify; `--force-all` bypasses; secret printing; concurrent uncoordinated applies on shared state.

---

**Related:** [master guide](./automation/platform-automation-master-guide.md) · [architecture](./automation/automation-architecture.md) · [cheat sheet](./automation/platform-automation-cheat-sheet.md)
