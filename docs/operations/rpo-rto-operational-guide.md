# RPO / RTO operational guide (lab measurements)

**Critical:** Values below are **Observed in Project 1** lab drills — **not production SLAs**.

Authoritative DR narrative: [dr-lab-evidence.md](../dr-lab-evidence.md), [disaster-recovery-master-guide.md](../disaster-recovery-master-guide.md).

---

## Definitions (operator)

| Term | Operator question |
|---|---|
| **RPO** | How much data/config can we lose? |
| **RTO** | How long until service is acceptable again? |

Measure with explicit timestamps **T0…T5** ([incident-timeline-template.md](./incident-timeline-template.md)).

---

## Observed recovery timings (Project 1)

| Scenario | RPO (lab) | RTO (lab) | Evidence |
|---|---|---|---|
| Pod delete (Deployment) | N/A (stateless pod) | ~**10–14 s** to Ready | Earlier VMware pod experiment |
| Argo selfHeal (annotation drift) | Config drift only | ~**6 s** | [dr-lab-evidence.md](../dr-lab-evidence.md) |
| Argo Application delete + re-apply | Git unchanged | ~**6–14 s** App Synced/Healthy; workloads may persist | dr-lab-evidence |
| Namespace delete + GitOps recreate | Declarative objects from Git; not runtime memory | ~**23 s** | dr-lab-evidence |
| Git bad commit → revert | **0** for committed desired state | ~**5–10 s** initial sync cited in DR docs | dr-lab-evidence / git-argo |
| EBS snapshot ReadyToUse | Point-in-time at snapshot | ~**72 s** | dr-lab-evidence |
| EBS restore PVC → Running | Restored volume = snapshot point (~74 s window demo) | ~**15 s** after capacity available | dr-lab-evidence |
| AWS worker failure + EBS reattach | EBS data on same volume (**Observed**) | ~**6.3 min** | [aws-storage-resilience.md](../aws-storage-resilience.md) |

---

## Configuration vs data RPO

| Plane | RPO in this lab | Source |
|---|---|---|
| **Configuration** (Deploy, Ingress, HPA, NP YAML) | **0** committed Git changes | Git + Argo |
| **EBS file data** | Time since last snapshot | Snapshot drill only |
| **local-path (VMware)** | **Design guidance:** no snapshot drill in Section 25 index for VMware PVC | [vmware-storage-statefulset.md](../vmware-storage-statefulset.md) |

---

## How to measure RTO on shift

| Step | Action |
|---|---|
| T0 | User impact or detection |
| T1 | Scope + evidence start |
| T2 | Remediation start (e.g. Git push revert) |
| T3 | Argo Synced / Deployment Available |
| T4 | `/health` 200 on user path |
| T5 | Declared stable |

Record in timeline; attach Argo revision and digest.

---

## Not tested in Project 1

| Scenario | Status |
|---|---|
| Full EKS cluster rebuild RTO | Plan-only / documented — [disaster-scenario-matrix.md](../disaster-scenario-matrix.md) |
| Region loss | **Not tested** |
| AWS Backup EKS restore | Assessed, on-demand backup **not executed** — [dr-lab-evidence.md](../dr-lab-evidence.md) |
| VMware control plane loss | **Not tested** |

---

## Related automation

Python DR helpers under `automation/python/src/platform_automation/dr/` — see [automation/platform-automation-master-guide.md](../automation/platform-automation-master-guide.md).
