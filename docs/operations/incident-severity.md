# Incident severity model (Project 1 operational model)

**Not** an official corporate standard — a **lab-aligned** severity scale for runbooks and postmortems.

| Severity | Definition | Examples (Project 1 context) |
|---|---|---|
| **SEV-1** | Broad unavailability or major data loss risk | All ingress/ALB paths down; both clusters broken; EBS data unrecoverable without snapshot |
| **SEV-2** | Major degradation or important function impaired | Single cluster app down; 50% replicas; failed rollout with user-visible errors; Argo control plane down while workloads run |
| **SEV-3** | Limited impact, workaround exists | One replica down with PDB; observability scrape down; advanced-lab Application Degraded |
| **SEV-4** | Minor / non-production | security-lab experiment failure; documentation-only issue |

---

## Mapping signals

| Signal | Typical severity |
|---|---|
| `/health` 200 on all user paths | SEV-4 or no incident |
| Partial replica loss, endpoints >0 | SEV-3 |
| Zero ready endpoints on `platform-lab` | SEV-2 → SEV-1 if prolonged |
| Git/Argo unavailable, workloads still running | SEV-2 (change pipeline blocked) |

---

## Response expectations (Design guidance)

| Severity | Communication | Technical response |
|---|---|---|
| SEV-1 | Immediate; incident commander | Stabilize first; [incident-response-playbook.md](./incident-response-playbook.md) |
| SEV-2 | Same shift | Triage matrix + Git rollback if deploy-related |
| SEV-3 | Next business window acceptable | Fix forward in Git |
| SEV-4 | Track in backlog | |

**Observed in Project 1:** Failed 0.1.5 rollout kept external path healthy via old ReplicaSet — likely **SEV-3** if detected early, **SEV-2** if new RS consumed capacity without serving.

Related: [escalation.md](./escalation.md)
