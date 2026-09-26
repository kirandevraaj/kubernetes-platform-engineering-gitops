# Postmortem: \<incident title\>

| Field | Value |
|---|---|
| **Date** | |
| **Duration** | |
| **Severity** | SEV- _ ([incident-severity.md](../operations/incident-severity.md)) |
| **Clusters** | `ckad-lab` / `platform-lab-aws` / both |

---

## Impact

Who/what was affected; user-visible symptoms; data impact (none / config / persistent).

## Detection

How discovered (monitor, user, manual check); time to detect.

## Timeline

Use [incident-timeline-template.md](../operations/incident-timeline-template.md) (T0–T6).

## Root cause

Technical root cause — factual, blameless.

## Contributing factors

Process, tooling, missing guardrails.

## Why existing controls failed

PDB, HPA, probes, GitOps, NetworkPolicy, backups — what did not help and why.

## Immediate fix

What restored service (include Git SHA / Argo revision if relevant).

## Permanent fix

Git/IaC/runbook/automation follow-ups.

## Detection improvement

Alerts, SLOs, synthetic checks (**Design guidance** if not implemented).

## Automation improvement

Python/Ansible/Jenkins changes.

## Runbook improvement

Links to updated runbooks.

## RTO / RPO (lab)

Measured recovery vs data loss window — label **Observed in Project 1** or **Not measured**.

Reference: [rpo-rto-operational-guide.md](../operations/rpo-rto-operational-guide.md), [dr-lab-evidence.md](../dr-lab-evidence.md).

## Lessons learned

- 

## Action items

| Action | Owner | Due |
|---|---|---|
| | | |

---

**Tone:** Blameless. Focus on systems and observability gaps.

Historical examples (Section 26): [`grafana-oom.md`](./grafana-oom.md), [`vmware-ingress-spof.md`](./vmware-ingress-spof.md), [`failed-rollout-0.1.5.md`](./failed-rollout-0.1.5.md), [`vmware-worker-failure.md`](./vmware-worker-failure.md), [`argo-comparison-error.md`](./argo-comparison-error.md), [`cross-namespace-snapshot-restore.md`](./cross-namespace-snapshot-restore.md).
