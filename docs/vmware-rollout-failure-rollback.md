# VMware Failed RollingUpdate and GitOps Rollback

**Date:** 2026-09-26  
**Environment:** VMware / on-prem kubeadm (`ckad-lab`)  
**Experiment type:** Intentional bad release → stuck RollingUpdate → Git digest rollback  
**AWS overlay:** digest briefly promoted then rolled back; bad `/health` gated to `APP_ENVIRONMENT=local-gitops` so EKS stays Ready on the same image  

---

## 1. Objective

Demonstrate the promotion and recovery path:

```text
Known-good 0.1.4
       ↓
CI build 0.1.5 (immutable digest)
       ↓
Argo CD promotion
       ↓
RollingUpdate (maxUnavailable=0, maxSurge=1)
       ↓
New pods fail readiness
       ↓
Old pods remain serving traffic
       ↓
Rollout becomes degraded / stuck
       ↓
Rollback Git to 0.1.4 digest
       ↓
Argo CD reconciles
       ↓
Known-good pods restored
```

This is **not** pod-delete self-healing and **not** annotation drift self-healing. It is **release safety**: readiness-gated rollout + GitOps rollback.

---

## 2. Digests and versions

| Release | Version label | Image digest |
|---|---|---|
| Known-good | `0.1.4` | `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` |
| Bad lab release | `0.1.5` | `sha256:945424e996f474c4cac45dd18c8c38319394a790ae00a2cd68c5ce9059461b96` |

Fault injected in `0.1.5` only when `APP_ENVIRONMENT=local-gitops` (VMware ConfigMap): `/health` returns **HTTP 503**.  
AWS ConfigMap uses `aws-eks-gitops`, so the same digest remains Ready there.

CI note: Jenkins UI was not used for this run (local Docker build/push + Git promotion commits mirroring the Jenkinsfile contract).

---

## 3. Baseline (known-good)

| Item | Value |
|---|---|
| Context | `ckad-lab` |
| Deployment | `platform-lab` **2/2** · digest `…872ff` |
| Strategy | RollingUpdate · `maxUnavailable: 0` · `maxSurge: 1` |
| `/health` | 200 |
| `/version` | `0.1.4` |
| Argo `platform-lab-local` | Synced / Healthy |

---

## 4. Bad release promotion

Commits:

1. `0c4fe12` — `feat: release 0.1.5 with intentional VMware readiness failure`
2. `6acbe3e` — `chore: promote platform-lab 0.1.5 digest to local and aws GitOps`

Argo refreshed desired state to digest `…1b96`. Deployment template updated; surge ReplicaSet created:

| ReplicaSet | Role | Ready |
|---|---|---|
| `platform-lab-9c5b867f` | old (0.1.4 digest) | **2/2** |
| `platform-lab-56ddf455bb` | new (0.1.5 digest) | **0/1** |

---

## 5. Stuck / degraded RollingUpdate

Observed within ~6s of sync:

| Field | Value |
|---|---|
| `replicas` | **3** (2 old + 1 surge) |
| `updatedReplicas` | **1** |
| `readyReplicas` / `availableReplicas` | **2** |
| `unavailableReplicas` | **1** |
| Service endpoints | **2** (old pods only) |
| Ingress `/health` | **200** (survivor traffic) |
| Ingress `/version` | **0.1.4** (old pods) |
| Argo health | **Synced / Progressing** → **Degraded** |

Why it sticks: with `maxUnavailable: 0`, Kubernetes will not terminate Ready old pods until a new pod becomes Ready. The new pod never passes readiness (`/health` → 503 on VMware), so the rollout cannot complete.

```text
Old RS (0.1.4)          New RS (0.1.5)
Pod A Ready ────────┐
Pod B Ready ────────┼──► Service endpoints (2)
                    │
Pod C NotReady ─────┘    (surge; not in Endpoints)
```

---

## 6. GitOps rollback

Commits:

1. `302a506` — `fix: rollback platform-lab overlays to known-good 0.1.4 digest`
2. `95820c8` — `revert: restore healthy 0.1.4 application source after readiness-failure lab`

Overlays restored:

- `digest: sha256:1cca2b59…872ff`
- `app.kubernetes.io/version: "0.1.4"`

Application source returned to healthy `/health` and `APP_VERSION=0.1.4` so `main` is not left carrying the lab fault. The bad `0.1.5` image remains on Docker Hub as a historical artifact only.

---

## 7. Recovery

After Argo hard refresh / reconcile (~6s):

| Item | Result |
|---|---|
| Deployment image | `…@sha256:1cca2b59…872ff` |
| Ready / updated | **2/2** |
| Bad RS `56ddf455bb` | scaled to **0** |
| Old RS `9c5b867f` | **2/2** again |
| Endpoints | **2** |
| Argo | **Synced / Healthy** |
| `/health` / `/version` | 200 / **0.1.4** |

No Deployment strategy change, no probe edit, no manual `kubectl rollout undo` — **Git desired state** drove the restore.

---

## 8. Comparison to prior labs

| Lab | Mechanism |
|---|---|
| Pod delete | ReplicaSet replaces Pod |
| Argo annotation/label drift | `selfHeal` restores live object to Git |
| **This lab** | Bad digest fails readiness → stuck surge → **Git rollback** of digest |

---

## 9. Lessons learned

1. **Readiness is a release gate.** A green image build is not a green rollout.
2. **`maxUnavailable: 0` preserves service** during a bad surge — old pods keep serving.
3. **Immutable digests make rollback precise** — pin Git to the last known-good digest.
4. **Argo health can show Progressing/Degraded** while Sync remains Synced (desired Git applied; Kubernetes progress incomplete).
5. **Environment-gated faults** let one digest be unsafe on VMware and safe on AWS for a dual-overlay promotion path.

---

## 10. Limitations

- Jenkins job was not exercised end-to-end (Docker Desktop build/push + Git commits mirrored the pipeline contract).
- New surge pod briefly showed `ContainerCreating` later in the window (node/pull timing); early samples already showed Running+NotReady with readiness failures.
- Bad `0.1.5` tag remains on Docker Hub; do not re-promote without fixing `/health`.

---

## Appendix — Commands

```powershell
kubectl config current-context   # ckad-lab
kubectl get deploy,rs,pods,endpoints -n platform-lab -o wide
kubectl get application platform-lab-local -n argocd
kubectl rollout status deploy/platform-lab -n platform-lab --timeout=30s
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/version
```
