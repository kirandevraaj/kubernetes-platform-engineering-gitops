# Argo CD OutOfSync Runbook (Project 1 — Section 26)

**Scope:** Application **OutOfSync** — live cluster differs from Git desired state.  
**Instances:** VMware Argo **v3.5.3**; AWS Argo **v3.1.0**.  
**Related:** [`argo-sync-failure.md`](./argo-sync-failure.md), [`gitops-change.md`](./gitops-change.md), [`git-argo-recovery.md`](./git-argo-recovery.md).

---

## Symptoms

- Argo UI: **OutOfSync** badge; diff view shows changed fields.
- `kubectl get application -n argocd` — `status.sync.status: OutOfSync`.
- May coexist with **Healthy** or **Degraded** health.

## Impact

- **Drift:** Cluster runs non-authoritative config until sync or selfHeal.
- **Audit:** Unknown who changed live objects (`kubectl edit`, controller, HPA).
- **Promotion block:** Some teams gate releases on Synced only.

## Severity

| Drift type | Severity |
|------------|----------|
| Labels/annotations only | **SEV-3** |
| Image/replicas/ingress | **SEV-2** |
| Security policy drift | **SEV-2** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get application <app> -n argocd -o jsonpath='{.status.sync.status}{"\n"}{.status.sync.revision}{"\n"}'`
2. Open Argo diff (UI or `argocd app diff` if CLI configured — no tokens in shell history).
3. **READ-ONLY:** Identify resource kinds out of sync (Deployment vs HPA-owned fields).

## Preconditions

- Confirm whether **selfHeal** is enabled on Application.
- Check **ignoreDifferences** for HPA/replica fields — may be expected **Design guidance**.

## Evidence

```powershell
kubectl get application <app> -n argocd -o yaml
# Compare live:
kubectl get deploy platform-lab -n platform-lab -o yaml
```

Record Git revision on Application vs `main` SHA.

## Triage

| Cause | Action |
|-------|--------|
| Intentional live patch | Revert live or commit to Git |
| selfHeal pending | Wait poll interval |
| New Git commit not synced | Sync or wait automated sync |
| Compare/render error | [`argo-sync-failure.md`](./argo-sync-failure.md) |

## Diagnosis

1. **Observed (Project 1):** Annotation drift on VMware reverted in **~6s** with selfHeal — [`vmware-argo-self-healing.md`](../vmware-argo-self-healing.md) / DR evidence.
2. HPA changes replica count — may show OutOfSync if not ignored.
3. Manual sync with **ApplyOutOfSyncOnly** (advanced lab) — production apps use standard sync options per Application manifest.

## Safe Remediation

| Goal | Method |
|------|--------|
| Git should win | Enable/wait **selfHeal**; or **Sync** Application (**WARNING — SAFE MUTATION** — applies Git to cluster) |
| Cluster hotfix should win | Commit equivalent change to Git first, then sync |
| Discard live drift | Sync from Git — do not leave cluster-only fix |

**WARNING — SAFE MUTATION:** `argocd app sync` / UI Sync applies cluster changes.

## Verification

- Status **Synced**; revision matches intended Git SHA.
- Workloads behave as expected (HTTP, replicas).

## Rollback

- Bad sync from bad Git: **Git revert** — [`git-rollback.md`](./git-rollback.md).
- Bad sync applied destructive manifest: revert Git + sync; use prune care on advanced options.

## Escalation

- Repeated drift: audit RBAC who can `kubectl edit`.
- ApplicationSet regenerating unexpected diffs — [`argocd-applicationset-troubleshooting.md`](./argocd-applicationset-troubleshooting.md).

## Do Not Do

- Sync with **Replace/Force** on production-like Applications.
- Store cluster-only hotfixes without Git follow-up.

## Expected Recovery

| Case | RTO |
|------|-----|
| selfHeal annotation drift | **~6s Observed** VMware |
| Manual sync after Git fix | seconds–minutes |

## Observed Project 1 Result

| Item | Status |
|------|--------|
| selfHeal restores drift | **Observed** VMware DR drill |
| OutOfSync during intentional bad digest (Synced but degraded rollout) | **Observed** — health ≠ sync |

## Postmortem Notes

- List fields drifted; was it human, HPA, or another controller?
- Update ignoreDifferences only with team review.
