# VMware Argo CD Drift Detection and Self-Healing

**Date:** 2026-09-26  
**Environment:** VMware / on-prem kubeadm (`ckad-lab`)  
**Experiment type:** Controlled live configuration drift (Git-managed Deployment field)  
**AWS:** not modified  
**Related prior experiment:** [vmware-pod-self-healing.md](./vmware-pod-self-healing.md) (Kubernetes ReplicaSet self-healing)

---

## 1. Objective

Prove **Argo CD GitOps self-healing** for `platform-lab-local`:

```text
Git desired state
      ↓
Argo CD (automated sync + selfHeal)
      ↓
Kubernetes live state
```

by intentionally mutating **live** Kubernetes state **outside Git**, then observing:

1. Argo detects **OutOfSync** (drift)
2. Argo **self-heals** (automated sync)
3. Live state returns to Git desired state
4. Application stays **Synced / Healthy**

This is **not** Kubernetes ReplicaSet self-healing (pod deletion). No pods were deleted.

---

## 2. GitOps Architecture

| Item | Value |
|---|---|
| Context | `ckad-lab` |
| Argo Application | `platform-lab-local` (namespace `argocd`) |
| Source repo | `https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git` |
| Source path | `kubernetes/overlays/local` |
| Target revision | `main` |
| Destination | in-cluster → namespace `platform-lab` |
| Automated sync | `prune: true`, **`selfHeal: true`** |
| Sync options | `CreateNamespace=true`, `ApplyOutOfSyncOnly=true` |
| ignoreDifferences | Deployment `/spec/replicas` only (HPA owns replica count) |
| Baseline revision | `7030f71` |
| Argo CD version | `v3.5.3` |

Desired application image (unchanged throughout):

`kirandevraaj/platform-lab@sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` · version **0.1.4**

---

## 3. Kubernetes Self-Healing vs Argo Self-Healing

| Mechanism | Trigger | Actor | What is restored |
|---|---|---|---|
| **Kubernetes native** | Pod deleted / crashed | ReplicaSet controller | Pod count / Ready pods |
| **Argo CD GitOps** | Live object ≠ Git desired | Argo application-controller (`selfHeal`) | Git-managed resource fields |

```text
Kubernetes:
  Pod deleted
    → ReplicaSet replaces Pod

Argo CD:
  Git/live drift
    → Argo detects OutOfSync
    → Argo reconciles resource from Git
```

The previous pod-failure lab proved the left column. This lab proves the right column.

---

## 4. Baseline State

| Item | Value |
|---|---|
| Argo sync / health | **Synced / Healthy** |
| Deployment | `platform-lab` **2/2** Ready |
| Label under test | `app.kubernetes.io/component=api` (matches Git) |
| Endpoints | **2** |
| HPA | min=2 max=4 · cpu ~4%/70% |
| `/health` | HTTP **200** |
| `/version` | **0.1.4** |
| Image digest | `sha256:1cca2b59…872ff` |

---

## 5. Drift Injection

### 5.1 Candidate that did **not** produce OutOfSync

First attempt: add a live-only annotation that is **absent from Git**:

```powershell
kubectl annotate deployment platform-lab -n platform-lab drift-test=true
```

| Observation | Result |
|---|---|
| Annotation present on live Deployment | Yes (`drift-test=true`) for ~180s |
| Argo sync status | Remained **Synced** |
| Hard refresh | Still **Synced** |
| Self-heal | Did **not** run |

**Diagnosis:** With this Argo CD compare path, an **extra** annotation key that does not exist in the desired (Git) manifest was **not** treated as sync drift. Git was unchanged; live had an unmanaged additive annotation. That is useful platform knowledge, but it is **not** a valid demonstration of OutOfSync → selfHeal.

The annotation was removed before the successful trial so no permanent live drift remained from this probe.

### 5.2 Successful drift target (Git-managed field)

Mutate a label that **is** declared in Git:

| Field | Git desired | Live mutation |
|---|---|---|
| `metadata.labels["app.kubernetes.io/component"]` | `api` | `api-drift` |

```powershell
kubectl label deployment platform-lab -n platform-lab `
  'app.kubernetes.io/component=api-drift' --overwrite
```

Constraints honored:

- Git **not** modified for the drift
- Image / replicas / probes / HPA / Service / NetworkPolicy untouched
- No pod deletion
- No manual `argocd app sync` / no manual revert

---

## 6. Argo CD Drift Detection

Measured trial (tight poll, ~300 ms):

| Time (UTC) | Elapsed | Sync | Live label | Operation |
|---|---|---|---|---|
| `2026-09-26T05:41:12.700Z` | T0 | Synced (pre) | `api` → mutate | label applied |
| `2026-09-26T05:41:12.924Z` | **0.22 s** | **OutOfSync** | already restored to `api` | automated sync **Running** |
| `2026-09-26T05:41:13.664Z` | **0.96 s** | **Synced** | `api` | automated sync **Succeeded** |

Argo Application events (same second):

```text
OperationStarted     Initiated automated sync to '7030f71…'
ResourceUpdated      Updated sync status: Synced -> OutOfSync
OperationCompleted   Partial sync operation … succeeded
ResourceUpdated      Updated sync status: OutOfSync -> Synced
```

Controller evidence:

- `initiatedBy.automated: true`
- `autoHealAttemptsCount: 3` (cumulative self-heal attempts on this Application)
- Sync result: `deployment.apps/platform-lab configured`

---

## 7. Argo CD Self-Healing

Sequence observed:

```text
Live label = api-drift (≠ Git)
        ↓
Application status → OutOfSync
        ↓
selfHeal automated sync (ApplyOutOfSyncOnly)
        ↓
Deployment patched from Git desired
        ↓
Live label = api
        ↓
Application status → Synced / Healthy
```

**Kubernetes ReplicaSet did not perform this reconciliation.** Pods were not replaced for this drift; the Deployment metadata label was corrected by Argo applying the Git manifest.

---

## 8. Timing Measurements

| Metric | Value |
|---|---|
| Time to detect OutOfSync | **~0.22 s** (first poll after mutate) |
| Time to restore label + Synced | **~0.96 s** |
| Manual sync used | **No** |
| Manual revert used | **No** |
| Git changed for drift | **No** |

Self-heal is near-instant when the controller is watching the object and `selfHeal: true` is enabled. OutOfSync is visible, but the window is sub-second — easy to miss without tight polling or event inspection.

---

## 9. Final Reconciled State

| Item | Value |
|---|---|
| Argo | **Synced / Healthy** |
| Label | `app.kubernetes.io/component=api` (matches Git) |
| `drift-test` annotation | **absent** |
| Deployment | **2/2** Ready |
| Endpoints | **2** |
| Revision | still `7030f71` (no new Git deploy required) |

Git before / after drift injection: **unchanged** (documentation commit is separate).

---

## 10. Application Health

| Check | Result |
|---|---|
| Pods Ready | `65xpb`, `dfd2m` · **2/2** Running |
| HPA | healthy · replicas=2 |
| PDB | present |
| `/health` | HTTP **200** throughout |
| `/version` | **0.1.4** |
| Image digest | unchanged `sha256:1cca2b59…872ff` |

No CrashLoopBackOff / OOMKilled / Evicted / MemoryPressure from this experiment.

---

## 11. Prometheus/Grafana Observation

Secondary only — not the source of truth for drift.

| Check | Result |
|---|---|
| `up{job="platform-lab"}` | **2** targets UP (`10.244.36.194`, `10.244.36.233`) |
| Grafana | No required panel change; app availability stayed healthy |
| Primary drift evidence | Argo Application status + events + controller logs |

---

## 12. Lessons Learned

1. **Argo self-heal ≠ ReplicaSet self-heal.** Pod deletion recovers via Kubernetes; Git/live field drift recovers via Argo.
2. **Choose a Git-managed field.** Mutating a label/value present in the desired manifest produces clear OutOfSync. Adding an **extra** live-only annotation did **not** in this lab.
3. **Self-heal can be sub-second.** Capture with events / controller logs / high-frequency polling; a 2–3 s poll loop can miss OutOfSync entirely.
4. **`selfHeal: true` + object watch** is what closed the loop — no human sync.
5. **`ignoreDifferences` for `/spec/replicas`** correctly leaves HPA free to scale without false drift; it did not hide the label change.
6. Observability (Prometheus/Grafana) confirms the app stayed up; Argo is the system of record for config drift.

---

## 13. Failure Modes

| Failure mode | What would happen |
|---|---|
| `selfHeal: false` | OutOfSync persists until manual sync |
| Drift only in ignored paths (e.g. `/spec/replicas`) | No OutOfSync (by design) |
| Live-only additive annotation (this lab) | May remain Synced — not healed |
| Git also changed to match bad live state | Sync would “succeed” by adopting the bad desired state |
| Manual sync during experiment | Confounds proof that automation healed |

---

## 14. Next Reliability Experiment

Candidates:

- Disable `selfHeal` temporarily (lab-only) to show stuck OutOfSync, then re-enable
- AWS EKS Argo Application drift comparison (separate env)
- Controlled ConfigMap drift that does not restart workloads
- Combine: pod failure (K8s heal) + config drift (Argo heal) in one narrative runbook

---

## Appendix — Commands used

```powershell
kubectl config current-context   # ckad-lab
kubectl get application platform-lab-local -n argocd
kubectl get deployment platform-lab -n platform-lab -o yaml

# Successful drift (live only — do not commit):
kubectl label deployment platform-lab -n platform-lab `
  'app.kubernetes.io/component=api-drift' --overwrite

# Observe (do not sync manually):
kubectl get application platform-lab-local -n argocd -w
kubectl get events -n argocd --field-selector involvedObject.name=platform-lab-local

# Verify restore:
# label back to api · Synced / Healthy
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/version
```
