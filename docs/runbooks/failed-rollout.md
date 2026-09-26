# Failed Rollout Runbook (Project 1 — Section 26)

**Scope:** Deployment **RollingUpdate** stuck, degraded, or incomplete — especially readiness-gated surges.  
**Primary reference:** [`vmware-rollout-failure-rollback.md`](../vmware-rollout-failure-rollback.md).  
**GitOps rollback:** [`git-rollback.md`](./git-rollback.md) — not `kubectl rollout undo` as primary.

---

## Symptoms

- `kubectl rollout status` hangs or reports progress deadline exceeded.
- `replicas` > desired (surge), `updatedReplicas` < desired, `unavailableReplicas` ≥ 1.
- Two ReplicaSets active: old **Ready**, new **NotReady**.
- Argo **Progressing** → **Degraded**; Sync may still be **Synced**.

## Impact

- **Observed:** With `maxUnavailable: 0`, **old pods keep serving** — user impact minimal during bad surge.
- Cluster carries extra surge pod (CPU/memory).
- Operators may confuse “Synced” with “rollout complete”.

## Severity

| Endpoints / HTTP | Severity |
|------------------|----------|
| Old Ready pods in Endpoints, HTTP OK | **SEV-3** |
| No Ready pods | **SEV-1** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get deploy,rs,pods,endpoints -n platform-lab -o wide`
2. **READ-ONLY:** `kubectl rollout status deploy/platform-lab -n platform-lab --timeout=30s`
3. **READ-ONLY:** `kubectl get application platform-lab-local -n argocd` (or `platform-lab-aws`)
4. Edge check: VMware VIP `/health` · AWS ALB `/health`

## Preconditions

- Identify **intentional lab fault** vs accidental promotion.
- Known-good digest: `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`.

## Evidence

```powershell
kubectl describe deploy platform-lab -n platform-lab
kubectl get rs -n platform-lab -o custom-columns=NAME:.metadata.name,DESIRED:.spec.replicas,READY:.status.readyReplicas,IMAGE:.spec.template.spec.containers[0].image
```

Save Git commits for promotion and Argo `status.sync.revision`.

## Triage

| Field | Meaning |
|-------|---------|
| New RS 0 Ready | Readiness/image/config — [`pod-not-ready.md`](./pod-not-ready.md) |
| ImagePullBackOff | Registry/digest |
| Progress deadline | Probe never green |
| Argo OutOfSync | Live drift — [`argo-outofsync.md`](./argo-outofsync.md) |

## Diagnosis

**Mechanism (Observed VMware 0.1.5):**

```text
maxUnavailable: 0  →  old pods not terminated until new Ready
new pod /health 503  →  never Ready  →  rollout stuck with surge
```

Within **~6s** of bad sync: 3 replicas (2 old + 1 surge), 2 available, endpoints **2**.

## Safe Remediation

1. **GitOps (preferred):** Revert overlay image digest and app version to **0.1.4** on `main`; push; refresh Argo Application.  
   **WARNING — SAFE MUTATION:** Git change — coordinate if multiple teams use branch.

2. Wait for Deployment to scale bad RS to 0 and restore updatedReplicas.

3. **Break-glass only:** pause rollout or undo via kubectl — then **immediately** align Git or selfHeal will revert/fight.

**Not tested as primary path:** `kubectl rollout undo deploy/platform-lab`.

## Verification

- `readyReplicas` == `spec.replicas`; single RS at desired count.
- Image `@sha256:1cca2b59…872ff` (full digest in Git).
- Argo **Synced / Healthy**; `/version` shows **0.1.4**.

## Rollback

Documented commits in lab: `302a506`, `95820c8` style revert on overlays + app source — see rollout doc.

## Escalation

- Jenkins/CI if promotions auto-merge bad digests.
- PDB conflicts if rollout never schedules surge — rare with lab settings.

## Do Not Do

- Scale old RS manually without Git change (Argo drift).
- Delete all pods to “force” rollout — risks brief outage if maxUnavailable > 0.
- Re-promote `0.1.5` fault without fixing VMware `/health` behavior.

## Expected Recovery

**Observed:** Argo reconcile **~6s** after Git restore; Deployment **2/2** Ready.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Stuck surge + Git digest rollback | **Observed** VMware |
| AWS unaffected (env-gated 503) | **Observed** |
| kubectl rollout undo as primary | **Not tested** — design rejects |

## Postmortem Notes

- Capture RS names, digests, and whether ingress showed old version throughout.
- Recommend digest pin + automated canary/readiness gate in CI.
