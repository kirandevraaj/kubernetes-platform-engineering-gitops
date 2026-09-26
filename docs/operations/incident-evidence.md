# Incident evidence collection standard

**Goal:** Preserve facts for diagnosis, recovery measurement, and postmortems — **without secrets**.

Related: [incident-timeline-template.md](./incident-timeline-template.md) · [incident-response-playbook.md](./incident-response-playbook.md)

---

## Required fields (minimum)

| Field | Example / source |
|---|---|
| Timestamp (UTC) | T0 detection |
| Cluster / context | `ckad-lab` or `platform-lab-aws` |
| Namespace | `platform-lab` |
| Application (Argo) | `platform-lab-local` / `platform-lab-aws` |
| Git SHA | `git rev-parse HEAD` (repo) |
| Argo sync revision | Application `.status.sync.revision` |
| Image digest | `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` |
| Pod status | `kubectl get pods -o wide` |
| Events | `kubectl get events --sort-by='.lastTimestamp'` |
| Deployment / RS | generations, available replicas |
| Service / EndpointSlice | address count |
| NetworkPolicy | policies in namespace |
| PVC / PV / VolumeAttachment | if storage-related |
| Node | conditions if node incident |
| AWS resource IDs | e.g. `vol-05faa26874d720ecd`, ALB target health — **no credentials** |

---

## READ-ONLY collection commands

| Purpose | Command | Class |
|---|---|---|
| Cluster snapshot | `kubectl get nodes,pods -A -o wide` | READ-ONLY |
| Argo | `kubectl get applications -n argocd -o wide` | READ-ONLY |
| App detail | `kubectl describe deploy,pod -n platform-lab` | READ-ONLY |
| Storage | `kubectl get pvc,pv,volumeattachment` | READ-ONLY |
| Logs (app) | `kubectl logs deploy/platform-lab -n platform-lab --tail=200` | READ-ONLY |

---

## Never capture

| Item | Reason |
|---|---|
| Secret values | Credential leak |
| `kubectl get secrets -o yaml` | Often contains tokens |
| kubeconfig file contents | Cluster credentials |
| AWS access keys / session tokens | Account compromise |
| Jenkins credential store | Same |
| Authorization headers from live traffic | May contain tokens |

**Design guidance:** Automated bundle via `platform-automate ops evidence` — **Not verified in this doc pass**; redaction rules in mission Phase 79 apply when implemented.

---

## Storage-specific evidence

Link measured drills: [dr-lab-evidence.md](../dr-lab-evidence.md), [aws-storage-resilience.md](../aws-storage-resilience.md), [vmware-storage-statefulset.md](../vmware-storage-statefulset.md).

| Scenario | Extra evidence |
|---|---|
| EBS attach | VolumeAttachment, PV AZ, EC2 volume state (describe-volumes) |
| Snapshot restore | VolumeSnapshot status, snapshot handle, restored volume ID |
| Node failure | Node NotReady time, pod reschedule time |

---

## Retention

**Design guidance:** Lab workstation folders under `evidence/<timestamp>/` — define team policy for production.
