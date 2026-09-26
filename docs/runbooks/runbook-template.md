# Runbook template (Project 1 — Section 26)

Use this structure for every operational runbook. Adapt sections when an incident needs extra detail (storage AZ, GitOps-only, security).

**Classification legend**

| Class | Meaning |
|---|---|
| **READ-ONLY** | No cluster/repo/infra mutation; safe during triage |
| **SAFE MUTATION** | Reversible or GitOps-aligned change with explicit target |
| **DESTRUCTIVE** | Irreversible or high blast-radius; requires WARNING, named target, confirmation, verification |

---

# Incident: \<title\>

| Field | Value |
|---|---|
| **Runbook owner** | Platform operator |
| **Environments** | VMware `ckad-lab` · AWS `platform-lab-aws` (separate where noted) |
| **Related** | Link architecture / experiment / DR doc |

## Symptoms

What users, monitors, or operators observe (HTTP codes, Argo status, Pod phase, alerts).

## Impact

Who is affected, blast radius, data/config risk. Label **Observed in Project 1** vs **Design guidance**.

## Severity

Map to [incident-severity.md](../operations/incident-severity.md) (Project 1 operational model, not corporate policy).

## First 60 Seconds

1. Confirm **context** (`kubectl config current-context`).
2. Classify layer ([triage-framework.md](../troubleshooting/triage-framework.md) STEP 1).
3. Run **READ-ONLY** health checks (Application, Deployment, ingress/ALB).
4. Note **recent Git/Argo/Jenkins/Terraform** activity.
5. Open incident channel; assign incident commander if SEV-1/2.

## Preconditions

- Correct kubeconfig context (VMware vs AWS tools container).
- No credentials in tickets or pasted command output.
- For **SAFE MUTATION** / **DESTRUCTIVE**: change ticket, rollback plan, named resource.

## Evidence to Collect

Follow [incident-evidence.md](../operations/incident-evidence.md). Capture timestamps T0… before mutating.

## Triage

Ordered checks (READ-ONLY first). Link [troubleshooting-matrix.md](../troubleshooting/troubleshooting-matrix.md).

## Diagnosis

Hypothesis, supporting commands/output, ruled-out layers.

## Safe Remediation

| Step | Command / action | Class |
|---|---|---|
| 1 | Example: `kubectl get application -n argocd` | READ-ONLY |
| 2 | Example: Git revert + push (GitOps rollback) | SAFE MUTATION |

**WARNING — DESTRUCTIVE:** Document only when unavoidable; state exact object name, why, and verification after.

## Verification

Success criteria (HTTP `/health`, Argo Synced/Healthy, Deployment available replicas, PVC Bound, Prometheus target UP).

## Rollback

**GitOps default:** Git rollback → Argo reconcile ([git-rollback.md](./git-rollback.md), [git-argo-recovery.md](./git-argo-recovery.md)).  
Do **not** treat `kubectl rollout undo` as the primary Project 1 recovery path for `platform-lab`.

## Escalation

When to escalate: [escalation.md](../operations/escalation.md).

## Do Not Do

- `kubectl edit` for durable app changes bypassing Git.
- Blind `terraform apply` / `terraform destroy`.
- Manual EBS attach/detach.
- Paste Secret values or tokens into evidence bundles.

## Expected Recovery

Design guidance or **Observed in Project 1** timings (link [rpo-rto-operational-guide.md](../operations/rpo-rto-operational-guide.md)).

## Observed Project 1 Result

Facts from lab experiments only; if not run, state **Not tested in Project 1**.

## Evidence

Paths to logs, commit SHAs, Argo revision, image digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` when relevant.

## Postmortem Notes

Link [postmortem-template.md](../postmortems/postmortem-template.md) if severity warrants.
