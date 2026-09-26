# Application Unhealthy Runbook (Project 1 — Section 26)

**Scope:** Argo CD Application health **Degraded**, **Progressing**, or **Missing** while workloads may still serve traffic.  
**Production-like apps:** `platform-lab-local` (VMware `ckad-lab`), `platform-lab-aws` (AWS EKS).  
**Known-good reference:** image digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` (`0.1.4`).  
**Related:** [`vmware-rollout-failure-rollback.md`](../vmware-rollout-failure-rollback.md), [`git-rollback.md`](./git-rollback.md), [`failed-rollout.md`](./failed-rollout.md).

---

## Symptoms

- Argo UI or `Application` status: **Health = Degraded** or **Progressing** (Sync may still be **Synced**).
- Deployment `readyReplicas` < desired; surge ReplicaSet with NotReady pods.
- Ingress/ALB returns mixed versions or intermittent errors.
- Prometheus `kube_deployment_status_replicas_available` below spec (if observability synced).

## Impact

- **User traffic:** May remain OK if old Ready pods still in Endpoints (`maxUnavailable: 0` lab default).
- **GitOps:** Desired state in Git is applied; Kubernetes rollout may be incomplete.
- **Ops:** False alarm if only Argo health lags while HTTP checks pass.

## Severity

| Condition | Severity |
|-----------|----------|
| Endpoints ≥ 1, HTTP `/health` 200 | **SEV-3** — investigate rollout |
| Endpoints 0 or sustained 5xx | **SEV-2** — page on-call |
| All clusters + Git bad on `main` | **SEV-1** — stop promotions |

## First 60 Seconds

1. **READ-ONLY:** `kubectl config current-context`
2. **READ-ONLY:** `kubectl get application -n argocd` (filter app name)
3. **READ-ONLY:** `kubectl get deploy,rs,pods,endpoints -n platform-lab -o wide`
4. **READ-ONLY:** HTTP check — VMware: `curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health` · AWS: ALB hostname `/health`
5. Decide: **traffic OK + stuck rollout** vs **no healthy backends**.

## Preconditions

- `kubectl` context matches intended cluster (VMware vs AWS are separate Argo instances).
- No active change window blocking sync (advanced lab sync windows — see [`argo-advanced-patterns.md`](../argo-advanced-patterns.md)).
- Do not paste Secrets or repo credentials into tickets.

## Evidence (collection)

```powershell
kubectl get application <app> -n argocd -o yaml
kubectl describe deploy platform-lab -n platform-lab
kubectl get events -n platform-lab --sort-by='.lastTimestamp' | Select-Object -Last 30
```

Argo: note `status.health`, `status.sync`, `status.operationState`, Git revision SHA.

## Triage

| Signal | Likely cause | Next runbook |
|--------|--------------|--------------|
| New RS NotReady, old RS Ready | Bad image/readiness | [`failed-rollout.md`](./failed-rollout.md) |
| Pods CrashLoopBackOff | App/config bug | [`pod-failure.md`](./pod-failure.md) |
| Pods Running, not Ready | Probe failure | [`pod-not-ready.md`](./pod-not-ready.md) |
| Argo OutOfSync | Drift or pending sync | [`argo-outofsync.md`](./argo-outofsync.md) |
| Sync error | Render/permission | [`argo-sync-failure.md`](./argo-sync-failure.md) |

## Diagnosis

1. Compare **live image digest** vs Git overlay (`kubernetes/overlays/local` or `aws`).
2. Inspect readiness probe logs: `kubectl logs -n platform-lab -l app.kubernetes.io/name=platform-lab --tail=50` (**READ-ONLY**).
3. Check PDB/HPA not blocking (READ-ONLY): `kubectl get pdb,hpa -n platform-lab`.
4. **Observed (Project 1):** Intentional `0.1.5` on VMware returned **503** on `/health` while Argo showed **Degraded**; **2/2** old pods kept serving — [`vmware-rollout-failure-rollback.md`](../vmware-rollout-failure-rollback.md).

## Safe Remediation

1. If bad Git promotion: **Git revert** to known-good digest → push → Argo sync (primary GitOps path). See [`git-rollback.md`](./git-rollback.md).  
   **WARNING — SAFE MUTATION:** Git revert on `main` affects all consumers of that overlay path.
2. If transient probe blip: wait one probe period; re-check endpoints (**READ-ONLY**).
3. If config-only fix needed: commit fix to Git; let Argo reconcile — avoid `kubectl edit` on production-like apps unless break-glass.

**Do not use as primary rollback:** `kubectl rollout undo` (bypasses Git SoT; Argo selfHeal may fight you).

## Verification

- Deployment: `readyReplicas == spec.replicas`, single active RS at desired digest.
- Endpoints count matches Ready pods.
- Argo: **Synced / Healthy**.
- `/health` 200 and `/version` matches Git tag (VMware VIP or AWS ALB).

## Rollback

**GitOps rollback (preferred):** revert overlay commits → refresh Application → verify.  
**Observed recovery:** ~6s Argo reconcile after `0.1.4` restore (VMware lab).

## Escalation

- Platform lead if `main` cannot be reverted quickly.
- Image/registry owner if digest pull failures.
- Section 25 DR if cluster API impaired: [`kubernetes-api-failure.md`](./kubernetes-api-failure.md).

## Do Not Do

- Delete Deployment or all pods at once on production-like apps without understanding surge/PDB.
- Force sync with **Replace/Force** on platform apps (advanced-lab only pattern).
- Re-promote known-bad `0.1.5` VMware fault image without fixing `/health` gating.

## Expected Recovery

| Path | RTO (lab order of magnitude) |
|------|--------------------------------|
| Git digest rollback | seconds–minutes (Argo poll + rollout) |
| Fix readiness in Git | one rollout cycle (~pod recreate **~10s** VMware observed for simple replace) |

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Stuck rollout + Git rollback `0.1.4` | **Observed** — VMware |
| Same digest healthy on AWS with env-gated fault | **Observed** — `APP_ENVIRONMENT=aws-eks-gitops` |
| Argo Degraded while ingress still 200 | **Observed** — readiness-gated surge |

## Postmortem Notes

- Record Git SHAs (bad + revert), Argo revision, digest, and whether traffic was impacted.
- Distinguish **Sync health** vs **HTTP SLO** in the incident timeline.
- Link follow-up: CI gate on readiness contract before digest promotion.
