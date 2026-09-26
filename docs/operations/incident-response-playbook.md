# Incident response playbook

**Flow:** Detect → Acknowledge → Scope → Preserve evidence → Stabilize → Diagnose → Remediate → Verify → Monitor → Close → Postmortem

Stabilization often beats immediate root-cause discovery (restore traffic via Git rollback before deep debugging).

---

## 1. Detect

| Source | Action |
|---|---|
| User report, `/health` failure, Argo Degraded, alert | Record **T0** UTC |
| Synthetic check | VMware: VIP `192.168.56.200`; AWS: ALB |

## 2. Acknowledge

Assign incident commander for SEV-1/2 ([incident-severity.md](./incident-severity.md)).  
Confirm **kubectl context** before any command.

## 3. Scope

Run [triage-framework.md](../troubleshooting/triage-framework.md) STEP 1–3.  
Document blast radius (namespaces, clusters, read vs write path).

## 4. Preserve evidence

[incident-evidence.md](./incident-evidence.md) — **before** mutations.  
Start [incident-timeline-template.md](./incident-timeline-template.md).

## 5. Stabilize

| Situation | Stabilization (prefer READ-ONLY first) |
|---|---|
| Bad deploy | Git revert known-good (`0.1.4` digest) → Argo |
| Live drift | selfHeal (**Observed** ~6s VMware) or Git sync |
| Zero endpoints | Fix readiness/probes via Git — not random pod delete |
| Ingress down | Check ingress-nginx / ALB targets |
| Argo ComparisonError | Fix manifest generation — no cluster “hammer” |

## 6. Diagnose

Use [troubleshooting-matrix.md](../troubleshooting/troubleshooting-matrix.md).  
Separate VMware vs AWS behavior (NetworkPolicy, ingress, storage).

## 7. Remediate

Smallest **SAFE MUTATION** aligned with GitOps.  
**DESTRUCTIVE** only with approval — [escalation.md](./escalation.md).

## 8. Verify

[post-change-checklist.md](../checklists/post-change-checklist.md) subset.  
Measure T5 − T0 for RTO notes ([rpo-rto-operational-guide.md](./rpo-rto-operational-guide.md)).

## 9. Monitor

Watch Argo, endpoints, error rate, HPA for 30–60 minutes (**Design guidance** duration).

## 10. Close

Update timeline T6; link runbook gaps.

## 11. Postmortem

SEV-1/2 or recurring SEV-3 → [postmortem-template.md](../postmortems/postmortem-template.md).

---

## DR incidents

Do **not** duplicate Section 25 procedures. Start at:

- [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md)
- [dr-lab-evidence.md](../dr-lab-evidence.md)
- [runbooks/disaster-recovery-index.md](../runbooks/disaster-recovery-index.md) when present

---

## Related runbooks (index)

| Area | Path |
|---|---|
| Application unhealthy | [runbooks/application-unhealthy.md](../runbooks/application-unhealthy.md) |
| Git / Argo | [runbooks/git-argo-recovery.md](../runbooks/git-argo-recovery.md) |
| Node failure | [runbooks/worker-node-failure.md](../runbooks/worker-node-failure.md) |
| Storage | [runbooks/pvc-pv-troubleshooting.md](../runbooks/pvc-pv-troubleshooting.md) |
