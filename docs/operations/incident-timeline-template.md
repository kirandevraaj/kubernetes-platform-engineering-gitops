# Incident timeline template

Use UTC timestamps. Align T-labels with [rpo-rto-operational-guide.md](./rpo-rto-operational-guide.md).

| Mark | Time (UTC) | Event | Evidence | Action | Owner |
|---|---|---|---|---|---|
| **T0** | | Detection (alert, user report, check failed) | | Acknowledge | |
| **T1** | | Scope classified ([triage-framework.md](../troubleshooting/triage-framework.md)) | | | |
| **T2** | | Evidence bundle started | | READ-ONLY collection | |
| **T3** | | Root cause hypothesis / confirmed | | | |
| **T4** | | Remediation started (smallest safe change) | | | |
| **T5** | | Service verified healthy | | | |
| **T6** | | Incident closed / monitoring handoff | | | |

---

## Example anchors (Observed in Project 1 — illustrative)

| Scenario | Reference timing |
|---|---|
| Pod delete → Ready | ~10–14 s |
| Argo selfHeal drift | ~6 s |
| Namespace delete → resynced | ~23 s |
| Argo App delete → re-applied Healthy | ~6–14 s |
| EBS snapshot ReadyToUse | ~72 s |
| Restore PVC → Pod Running | ~15 s |
| AWS worker failure + EBS reattach path | ~6.3 min |

Full DR tables: [dr-lab-evidence.md](../dr-lab-evidence.md) — **do not duplicate** full drill narrative here.

---

## Post-close

- Link postmortem: [postmortem-template.md](../postmortems/postmortem-template.md)
- Update [observed-vs-untested.md](./observed-vs-untested.md) if new evidence
