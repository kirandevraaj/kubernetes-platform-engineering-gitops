# Platform Automation Master Guide

**Status:** Section 24 MASTER REFERENCE for the Kubernetes Platform Engineering & GitOps Lab.

**Clusters:** VMware `ckad-lab` (1.31.x) · AWS `platform-lab-aws` (EKS 1.36.x)  
**Safe namespaces:** `automation-lab`, `security-lab`, `argo-advanced-lab`  
**Pinned clients:** `kubernetes==32.0.1`, `boto3==1.40.18`, `ansible-runner==2.4.1`, ansible-core `2.18.6`  
**App image (do not change in this milestone):** `kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

This guide answers interview-level **why** questions using Project 1 architecture. Companion Q&A: [automation-interview-notes.md](../automation-interview-notes.md).

---

## Part I — Automation Mental Model

### 1. Why Automation

Platform automation exists to make repeatable, auditable changes faster than humans clicking consoles—without sacrificing safety. In Project 1 the platform already spans VMware `ckad-lab` (Kubernetes 1.31.x), AWS EKS `platform-lab-aws` (1.36.x), Jenkins CI, Argo CD, and Terraform under `terraform/aws`.

Automation is not scripts that casually mutate production. It is a discipline: discover actual state, compare to desired state, apply idempotently, verify, and leave evidence. The payoff is fewer snowflake fixes and clearer interview stories grounded in this lab.

### 2. Imperative vs Declarative

**Imperative** means do these steps (create X, then patch Y). **Declarative** means make the world look like this (manifest, Terraform config, Ansible state modules).

Project 1 mixes both carefully: Python may be imperative orchestration, while Ansible modules, Terraform, Kubernetes manifests, and Argo CD are declarative engines. Prefer declarative desired state for anything that must converge continuously—especially `platform-lab` overlays reconciled by Argo CD.

### 3. Desired vs Actual State

**Desired** is what Git/config says should exist. **Actual** is what APIs return now. Automation computes a plan from the gap.

Example: desired Deployment image digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` in overlays vs live pods. Argo CD continuously closes that gap for GitOps apps; Python closes gaps for operational lab objects in `automation-lab`.

### 4. Idempotency

Idempotency means re-running the same automation does not accumulate damage or duplicates. `changed=false` and empty plans are success.

Without idempotency, retries create duplicate firewall rules, double EC2 tags, or conflicting objects. Ansible modules, Terraform, and Kubernetes apply/patch patterns exist primarily to encode idempotent convergence.

### 5. Reconciliation

Reconciliation is the loop that repeatedly drives actual toward desired. Argo CD reconciles Git to cluster with prune/self-heal on apps like `platform-lab-local` and `platform-lab-aws`.

Python reconciliation is usually on-demand (`platform-automate reconcile`) for ops tasks. Do not run a second reconciler that fights Argo on the same objects.

### 6. Eventual Consistency

Eventual consistency means systems report success before all observers see the final state (AWS describe lag, Kubernetes pod Ready delay, NSX realization).

Automation must wait and verify instead of trusting the first mutate response. Timeouts, retries, and PASS/FAIL/UNKNOWN verification exist because of eventual consistency.

## Part II — Python

### 7. Python Runtime

CPython 3.14.6 executes lab automation in `automation/python/.venv`. Treat the process exit code as the contract with Jenkins and humans.

Keep runtime pinned; casual upgrades change client behavior across VMware 1.31 and EKS 1.36.

### 8. Project Structure

Separate CLI, controller, adapters, and models. Dependency-inject AWS/K8s/Ansible clients so tests do not need live clouds.

Put non-secret defaults under `config/`; keep secrets in env/CI credentials only.

### 9. Virtual Environments

Virtualenvs isolate pins (`kubernetes==32.0.1`, `boto3==1.40.18`, `ansible-runner==2.4.1`) from system Python.

Recreate from `requirements.txt` rather than mutating global site-packages.

### 10. Dependencies

Pin direct dependencies with `==`. Document transitive risk in `toolchain-inventory.md`.

Refuse installing unpinned latest packages during demos—reproducibility beats novelty.

### 11. CLI

CLI verbs: doctor, inventory, validate, plan, reconcile, verify, report. Flags: `--dry-run`, `--confirm`, `--timeout`, `--max-retries`, `--context`, `--environment`.

Mutations require `--confirm`; never ship `--force-all`.

### 12. Configuration

Config precedence: CLI > env > file > defaults. Validate allow-listed contexts and namespaces before any write.

Forbidden targets include `platform-lab`, `storage-lab`, observability stacks, VPC/EKS/ALB.

### 13. Logging

Use logging with `run_id` and phases. DEBUG for retries; ERROR for denials; never log tokens.

Archive human and JSON logs from Jenkins for auditability.

### 14. Exceptions

Catch narrow SDK exceptions at adapters; map to domain errors; chain causes.

Bare `except` and silent pass hide partial failure—unacceptable in platform automation.

### 15. Subprocess

`subprocess.run` with argv lists, timeouts, and returncode classification. Prefer Ansible Runner for playbooks.

`shell=True` only when documented and inputs are constants—default deny.

### 16. REST

REST clients need base URL, auth from env, timeouts, JSON codecs, and retry on transient HTTP statuses.

Mock NSX Manager REST uses the same client shape as real fabric APIs.

### 17. JSON/YAML

JSON for machine reports and API payloads; YAML for Ansible and human config. Always `safe_load`.

Round-trip inventory and verify results as JSON artifacts.

### 18. Testing

pytest unit tests for plan/diff logic; contract tests with mocked `ApiException`/`ClientError`; optional live read-only doctor.

CI fails on unit/lint before any lab mutate.

### 19. Mocking

Mock adapters at interfaces, not inside deep business branches. Fake paginators and watch streams in unit tests.

Record/replay can help contract tests but must scrub secrets.

### 20. Retry

Retry throttles, connection resets, and conflicts; not 403/401/validation errors. Exponential backoff + jitter + max-retries.

Log every attempt into the run report.

### 21. Timeout

Per-call and wall-clock timeouts on HTTP, SDK, and subprocesses. Hung EKS calls must fail closed.

Align CLI `--timeout` with Runner and boto3 configs.

### 22. Concurrency

Concurrent reads OK; serialize conflicting writes. Measure forks vs threads in performance labs.

Concurrency multiplies rate-limit exposure—pair with budgets.

### 23. Asyncio

asyncio helps many concurrent IO waits, but boto3/kubernetes clients are largely sync; thread pools are pragmatic.

Do not rewrite Ansible itself in asyncio—orchestrate it as a subprocess/Runner job.

### 24. Security

No secrets in Git; least privilege IAM/RBAC; TLS verify on; confirm gates; refuse wrong context.

Automation security is part of platform security—same mindset as `docs/security-rbac.md`.

## Part III — Kubernetes Automation

### 25. Kubernetes API

Kubernetes exposes a versioned HTTP API. Controllers and kubectl are API clients; so is the Python client.

Lab API servers: `ckad-lab` 1.31.x and EKS 1.36.x—Core/Apps resources remain the automation focus.

### 26. Python Client

Package `kubernetes==32.0.1` matches lab adjacency and keeps patch/watch behavior stable.

Prefer client over kubectl subprocess for structure, mocks, and errors.

### 27. Authentication

Workstation auth via kubeconfig context (`ckad-lab` or AWS tools context). Impersonation unused by default.

Future in-cluster agents would use ServiceAccount tokens with minimal RBAC—never cluster-admin for lab bots.

### 28. Resource Models

Model resources as objects with apiVersion/kind/metadata/spec/status. Desired specs live in Git for GitOps apps.

Python dataclasses mirror subset fields needed for diff—do not reimplement the whole OpenAPI.

### 29. CRUD

Create/Read/Update/Delete via typed APIs. Prefer create-or-patch for idempotency in `automation-lab` only.

Do not delete `platform-lab` or storage objects.

### 30. Patch vs Replace

Patch merges changes; replace sends full objects and can drop fields. Strategic/merge/JSON patch each have tradeoffs.

For GitOps-managed apps, patching live is a smell—change Git instead.

### 31. Watch

Watch streams notify on changes. Useful for wait-until-Ready loops; must handle timeouts and resourceVersion resets.

Do not leave immortal watches in short CLI runs without budgets.

### 32. Wait

Wait for conditions (Available, Ready) with timeout. UNKNOWN if timeout; FAIL if terminal error.

Mirrors NSX realization waiting.

### 33. RBAC

RBAC binds subjects to verbs on resources. Automation should use least privilege Roles in lab namespaces.

403 is not retryable—fix RBAC, do not hammer the API.

### 34. Idempotency

Idempotent ensure: get, create if 404, patch if drift. Conflict 409 leads to refresh then limited retry.

Same idea as Ansible `kubernetes.core.k8s` with `state: present`.

### 35. Drift

Drift is actual not equal to desired. Argo detects Git drift for apps; Python detects ops drift for lab objects.

Self-heal on `platform-lab-local` restores Git—manual kubectl edits are temporary.

## Part IV — AWS Automation

### 36. Boto3

Boto3 is the AWS SDK for Python—preferred over shelling aws CLI for automation logic.

Pin `boto3==1.40.18` with botocore for reproducible errors/pagination.

### 37. Sessions

`Session(profile_name=..., region_name=...)` centralizes credentials from env/shared config.

Wrong profile fails doctor early.

### 38. Clients

Clients map to service APIs (eks, ec2, iam). Use for explicit calls and paginators.

Read-mostly for inventory in this milestone.

### 39. Resources

Resources offer object-like helpers; still backed by clients. Prefer clients when error codes matter.

Do not hide IAM failures inside generic resource exceptions without logging codes.

### 40. Paginators

Paginators iterate all pages for describe APIs. Always paginate inventory—first page is not truth.

Generators keep memory flat.

### 41. Errors

`ClientError` codes classify Auth/Throttle/NotFound. Map into domain errors like K8s `ApiException` handling.

Print Code and RequestId in reports—not secret material.

### 42. Retries

botocore retry modes help; still wrap with app-level max-retries and budgets.

Do not retry AccessDenied.

### 43. IAM

IAM is the authorization plane for AWS automation. Least privilege profiles; no long-lived keys in Git.

Separate read inventory role from any tagged mutate role.

### 44. EKS

EKS clusters are Terraform-created in Project 1. Python may describe cluster endpoint/status—not recreate control planes.

Kubeconfig for EKS is consumed by the Kubernetes client after AWS auth.

### 45. EC2

EC2 describe by tags feeds dynamic inventory thinking. Public IPs are ephemeral—tag-based identity wins.

Do not terminate instances via casual scripts.

### 46. VPC

VPC topology is Terraform-owned (`terraform/aws`). Automation may read for reports; must not rewrite CIDRs with boto3.

Boundary prevents shadow networking.

### 47. Safe mutation

Safe mutation: dry-run when supported, tag gates, `--confirm`, tiny blast radius. Never mutate ALB/EKS/VPC here.

Prefer changing Terraform code plus plan/apply for infra lifecycle.

## Part V — Ansible

### 48. Architecture

Control node runs Ansible against inventory using modules on managed nodes or localhost.

Project inventory lives under `automation/ansible/`.

### 49. Inventory

Static `hosts.yml` for localhost lab; optional readonly VMware workers; `aws_ec2` for tagged AWS hosts.

Inventory is membership, not desired config.

### 50. Ad-hoc

Ad-hoc ping/setup for doctor. Persistent state belongs in playbooks.

Ad-hoc mutation of workers is forbidden.

### 51. Playbooks

Playbooks declare plays: hosts, facts, tasks, handlers. Keep plays small and purpose-built.

Capstone: baseline/validate—not the entire platform.

### 52. Tasks

Tasks call modules in order. Name them for Runner logs.

Failed task stops the play unless rescued.

### 53. Modules

Modules encapsulate idempotent operations. Prefer collection modules over raw shell.

`kubernetes.core` and `amazon.aws` are pinned in `requirements.yml`.

### 54. Facts

Facts describe actual hosts. Use `when:` on facts; refresh when stale.

API-only targets may skip heavy fact gathering.

### 55. Variables

Variables parameterize plays. Secrets via Vault/CI. `extra_vars` from Python for run scope.

Avoid duplicate definitions across layers.

### 56. Precedence

Precedence determines which var wins. Operational rule: Python `extra_vars` override inventory defaults for a run.

Interview depth: know that `extra_vars` sit at the top of the precedence chain.

### 57. Templates

Jinja templates render files from vars. Use on localhost lab configs—not to overwrite Argo-managed manifests casually.

Template changes should notify handlers.

### 58. Loops

Loops reduce duplication. Bound concurrency against cloud APIs.

Clear `loop_var` names aid readability.

### 59. Conditionals

`when:` skips work safely—for example `lab_readonly` on `vmware_workers`.

Conditionals are safety controls, not just sugar.

### 60. Register

`register:` captures module results for later tasks and `failed_when`.

Python can also parse Runner events instead of only Ansible registers.

### 61. Handlers

Handlers run on notify when something changed—restart once per play.

Preserve idempotency of service management.

### 62. Roles

Roles package reusable automation. defaults vs vars discipline matters.

Small roles beat monolith roles.

### 63. Collections

Collections distribute modules/plugins. Install to `./collections` with pinned versions.

`ansible-core` alone is not enough for AWS/K8s modules.

### 64. FQCN

FQCN removes ambiguity and satisfies ansible-lint.

Write `ansible.builtin.copy` not bare `copy`.

### 65. Check Mode

Check mode predicts changes. Use before `--confirm` apply from Python.

Not all modules support check equally—know limitations.

### 66. Diff Mode

Diff mode shows before/after. Archive in CI for review.

Combine with check mode in dry-run stages.

### 67. Idempotency

Idempotent plays converge. `shell`/`command` need guards or avoidance.

`changed_when`/`creates` are escape hatches, not defaults.

### 68. Error Handling

`fail`, `assert`, `any_errors_fatal`, `ignore_errors` (rare). Prefer fail-visible.

Map failures to Python exit codes.

### 69. Blocks

`block`/`rescue`/`always` for structured cleanup and compensating logic.

Rescue should not hide permanent misconfiguration.

### 70. Delegation

`delegate_to` runs tasks elsewhere—often localhost API calls while iterating hosts.

Do not delegate OS mutation onto Kubernetes workers.

### 71. Serial

`serial:` rolling batch size for host changes. Matches upgrade-wave thinking.

Use with health checks between batches.

### 72. Strategies

Strategies (linear, free) and forks control parallelism.

Tune carefully versus AWS rate limits.

### 73. AWS Dynamic Inventory

`amazon.aws.aws_ec2` dynamic inventory keyed by tags replaces brittle IP lists.

Still read-mostly unless tags mark mutable lab instances.

### 74. Kubernetes Collection

`kubernetes.core` applies YAML declaratively. Limit to `automation-lab` teaching.

Production apps remain Git to Argo CD—not Ansible apply to `platform-lab`.

### 75. Vault

Vault encrypts secrets at rest. Unlock via env/CI—never commit passwords.

Prefer not putting production secrets in vault files in this lab repo.

### 76. Linting

`ansible-lint` in CI blocks risky patterns and missing FQCN.

Treat lint like ruff for playbooks.

### 77. Testing

Syntax-check, lint, check-mode, and pytest-around-Runner form the test story.

Live tests default to localhost.

## Part VI — Python + Ansible

### 78. Subprocess

Raw subprocess `ansible-playbook` works but is brittle to parse. Use for doctor only if needed.

Always argv plus timeout.

### 79. Ansible Runner

Ansible Runner is the supported software bridge: Python invokes Ansible safely with private data dirs and events.

Pin `ansible-runner==2.4.1`.

### 80. Runner events

Runner events stream task ok/changed/failed/unreachable. Drive reports and early abort.

Do not scrape ANSI colors from stdout as primary signal.

### 81. Orchestration

Orchestration: Python decides; Ansible executes bounded config; Python continues.

Keep playbooks dumb and controllers smart.

### 82. Verification

After Runner, verify with K8s/AWS/local asserts. Ansible `changed` is not the same as verified.

Verify returns PASS/FAIL/UNKNOWN.

## Part VII — Infrastructure Automation

### 83. Terraform

Terraform declaratively creates AWS infra in `terraform/aws` (VPC, EKS, IAM, LB controller, Argo bootstrap).

It is not for app Deployment image bumps—that is Git overlays plus Argo.

### 84. Plan

`terraform plan` is the infra analogue of `platform-automate plan`. Review before apply.

Automation may wrap plan; humans (or gated CI) approve apply.

### 85. Apply

Apply mutates real AWS. Out of band from app CI. Never from casual Python without gates.

State lock protects concurrency.

### 86. Safety

Safety: remote state, locking, least IAM, plan artifacts, no destroy in lab docs without warnings.

Do not let Ansible recreate Terraform resources.

### 87. State

State maps resources to real IDs. Corrupting state is an outage-class event.

Python should not edit state files.

### 88. Automation boundaries

Boundary: Terraform equals infra lifecycle; Ansible equals config; Python equals logic; Argo equals K8s desired; Jenkins equals CI.

Crossing boundaries creates drift fights.

## Part VIII — CI/CD

### 89. Jenkins

Jenkins on Docker Desktop runs `jenkins/Jenkinsfile`: test, build, push, promote digests for `platform-lab`.

Separate automation pipeline stages lint/dry-run/lab execute.

### 90. Credentials

Credentials IDs (`dockerhub-platform-lab`, `github-platform-lab`) live in Jenkins—not Git.

Same rule for AWS keys and kube tokens.

### 91. Pipeline

Pipeline: checkout, tests, lint, dry-run, plan, optional confirm lab, verify, archive.

`disableConcurrentBuilds` where promotions race.

### 92. Testing

Test automation itself: pytest, ruff, ansible-lint, check mode. App unit tests remain for `app/**`.

Fail closed before mutate.

### 93. Automation execution

Jenkins may execute `platform-automate` against `automation-lab`. It must not `kubectl apply` `platform-lab`.

GitOps promotion remains digest commits only.

## Part IX — GitOps

### 94. Git as Source of Truth

Git is source of truth for manifests, Terraform code, Argo Applications, and automation sources.

Live-only changes are debt.

### 95. Jenkins vs Argo CD

Jenkins equals CI/artifact/promotion commits. Argo CD equals CD reconcile/self-heal. See ADR-006.

Argo does not build images; Jenkins does not sync clusters.

### 96. Desired State

Desired state for apps includes digest-pinned images for `0.1.4` / `sha256:1cca2b…`.

Changing desired state means changing Git.

### 97. Direct Deployment Anti-pattern

Direct Jenkins to Kubernetes deploy is an anti-pattern: bypasses Git audit, races self-heal, breaks dual-env digest parity, weakens rollback.

Lab rule: never `kubectl apply` production app desired state from CI.

### 98. Promotion

Promotion: publish immutable digest once; commit both overlays; each Argo instance syncs its cluster.

Tag `latest` is forbidden.

## Part X — Production Automation

### 99. Security

Security: secret hygiene, least privilege, confirm gates, allow-lists, lint, no force flags.

Review automation like production code.

### 100. Observability

Observability: structured logs, reports, exit codes, archived artifacts. Optional metrics later.

Tie failures to runbooks.

### 101. Retries

Retries for transient faults only, with caps and jitter.

Document policy in CLI help.

### 102. Timeouts

Timeouts everywhere—APIs, Runner, global CLI.

Prefer FAIL/UNKNOWN over hanging SUCCESS.

### 103. Rate Limiting

Rate limiting: respect AWS and API server budgets; backoff; reduce forks.

Inventory caching helps.

### 104. Concurrency

Concurrency for independent reads; careful writes; Ansible forks dial.

Test under load in the performance lab.

### 105. Partial Failure

Partial failure: some hosts OK, some failed—exit `5`, report per-target, do not claim full success.

Rescue should mark unfinished work.

### 106. Rollback

Rollback: reverse plan, `git revert` plus Argo, or compensating API. No blind destroy-all.

Save prior snapshots before mutate.

### 107. Auditability

Auditability: who/what/when/`run_id`/plan/diff/results in Jenkins archives and Git history.

Secrets redacted.

### 108. Testing

Test pyramid plus failure injection (wrong context, denied IAM, timeouts) before trusting automation.

Record matrix in failure lab notes.

## Part XI — VMware/NSX Bridge

### 109. VMware automation

VMware automation historically meant PowerCLI/API against vCenter inventory and VM lifecycle.

Map to discovery/desired/idempotent apply/verify—same as Section 24 Python loops.

### 110. NSX automation

NSX automation is Manager REST: TN, Edge, segments, DFW. Practice on mocks; do not require live fabric.

See `vmware-nsx-automation-bridge.md`.

### 111. REST workflows

REST workflows: auth, list, put/patch, poll realization, verify. Identical skeleton to K8s/AWS adapters.

Encode timeouts and retries.

### 112. Desired-state thinking

Desired-state thinking replaces click-ops tribal knowledge with declared YAML and diffs.

Upgrade waves become orchestrated serial plans with health gates.

### 113. Migration to modern Platform Engineering

Modern platform engineering adds GitOps for Kubernetes and Terraform for cloud infra beside fabric APIs.

Your NSX skills transfer; tools change, loop does not.

## Part XII — Capstone

### 114. Architecture

Capstone architecture: CLI to config to discover to validate to plan to apply to verify to report with adapters for K8s/AWS/Ansible/Terraform.

Mutate only `automation-lab`.

### 115. Components

Components: `PlatformController`, adapters, Ansible roles, Jenkins pipeline, optional Git commit path for lab manifests.

Dependency injection for clients.

### 116. Workflow

Workflow commands: doctor, inventory, validate, plan, reconcile `--confirm`, verify, report.

Dry-run default mindset.

### 117. Validation

Validation rejects bad context/namespace/config before plan. Verify checks namespace/deploy/service/ready.

PASS/FAIL/UNKNOWN.

### 118. Failure Handling

Failure handling records input, error, recovery, exit code—feeds runbooks.

Abort waves on verify FAIL.

### 119. Security

Security: confirm gate, no force-all, secrets in CI, lint, allow-lists.

Same as production automation expectations.

### 120. CI/CD

CI/CD runs tests/lint/dry-run/lab execute/archive. No `platform-lab` kubectl apply.

App image digest remains `0.1.4` / `sha256:1cca2b…` unless a separate app release.

### 121. GitOps

GitOps: if capstone changes desired K8s state, commit Git and let Argo sync lab apps—not direct prod deploy.

Keep AppProject boundaries.

### 122. Operational Runbooks

Operational runbooks under `docs/runbooks/` cover automation, Python, Ansible, AWS API, Kubernetes API failures.

Use them in interviews as evidence of operability.

## Part XIII — Interview Reference

### 123. Core Questions

Core questions (why Python/Ansible/Terraform/Argo/Jenkins, idempotency, Runner, Vault, check/diff) are answered in `automation-interview-notes.md` with Project 1 specifics.

Memorize boundaries more than flags.

### 124. Scenario Questions

Scenario: partial Edge upgrade failure means stop waves, verify, rollback plan—same as serial Ansible failure plus Python controller abort.

Scenario: Jenkins wants kubectl apply—refuse; promote digest via Git.

### 125. Architecture Questions

Architecture: draw Git to Terraform/Argo and separate Python to Ansible ops; cite ADR-006 and dual Argo instances.

Explain digest pinning and dual overlays.

### 126. Troubleshooting Questions

Troubleshooting: wrong kube context, IAM AccessDenied, Runner failed events, Argo OutOfSync versus automation drift.

Start with doctor, inventory, and the last report artifact.

---

## Embedded mastery checklist (35)

Each item is answered in [automation-interview-notes.md](../automation-interview-notes.md) and reinforced in the numbered sections above:

1. Why Python for infrastructure automation?
2. Why Ansible?
3. Python vs Ansible?
4. Boto3 vs AWS CLI?
5. Kubernetes Python client vs kubectl?
6. Why idempotency?
7. What is variable precedence?
8. What are handlers?
9. What are roles?
10. What are collections?
11. Why FQCN?
12. What is dynamic inventory?
13. What is check mode?
14. What is diff mode?
15. What is Ansible Vault?
16. How does Ansible handle failure?
17. What is delegation?
18. What is Ansible Runner?
19. Where does Terraform fit?
20. Where does Jenkins fit?
21. Where does Argo CD fit?
22. How do you prevent direct Jenkins-to-Kubernetes deployment?
23. How do you design safe automation?
24. How do you test infrastructure automation?
25. How do you handle API rate limiting?
26. How do you implement retries?
27. How do you prevent duplicate resource creation?
28. How do you detect drift?
29. What is eventual consistency?
30. How would you automate VMware/NSX?
31. How would you automate an EKS platform?
32. How would you handle partial failure?
33. How do you protect credentials?
34. How do you design rollback?
35. What should never be automated blindly?

---

## Related diagrams and runbooks

- [automation-architecture.md](./automation-architecture.md)
- [diagrams/](../diagrams/)
- [runbooks/](../runbooks/)
- [toolchain-inventory.md](../toolchain-inventory.md)
- Operations: [platform-operations-handbook.md](../operations/platform-operations-handbook.md) · [python-automation-failure.md](../runbooks/python-automation-failure.md) · [ansible-failure.md](../runbooks/ansible-failure.md)
- CLI ops: `platform-automate doctor|ops health|ops triage|ops report|ops evidence` (read-only)
