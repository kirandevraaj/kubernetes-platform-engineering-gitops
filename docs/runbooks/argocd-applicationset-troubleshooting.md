# Argo CD ApplicationSet Troubleshooting (Project 1 — Section 26)

**Scope:** ApplicationSet controller issues — missing generated Applications, duplicate apps, owner conflicts, generator errors.  
**Lab objects:** `platform-advanced-set`, `platform-advanced-git-set`, nested sets under App-of-ApplicationSets — [`argo-advanced-patterns.md`](../argo-advanced-patterns.md).  
**Not in scope:** Renaming production `platform-lab-*` Applications.

---

## Symptoms

- Expected Application from generator missing (`kubectl get applications -n argocd`).
- ApplicationSet **Error** status or controller logs show template/render failure.
- Deleted generated Application reappears immediately.
- Git generator produces overlapping or empty parameter sets.

## Impact

- Advanced lab envs (`argo-advanced-dev`, etc.) not provisioned.
- **Observed:** Manual delete of generated app **regenerated** by owner reference — expected controller behavior.
- Production fleet unaffected when generators scoped to `platform-advanced-lab` project.

## Severity

| Area | Severity |
|------|----------|
| Advanced lab only | **SEV-4** |
| Bootstrap ApplicationSet for platform | **SEV-2** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get applicationset -n argocd`
2. **READ-ONLY:** `kubectl get application -n argocd -l app.kubernetes.io/part-of=platform-advanced-lab` (label if present; else grep `platform-advanced`)
3. **READ-ONLY:** `kubectl describe applicationset <name> -n argocd`

## Preconditions

- ApplicationSet template must reference allowed **AppProject** (`platform-advanced-lab`).
- List generator preferred over Git generator for stable names in this lab — **Design guidance** from advanced doc.

## Evidence

```powershell
kubectl get applicationset <name> -n argocd -o yaml
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-applicationset-controller --tail=80
```

Record generator type (list, git, cluster) and template errors.

## Triage

| Symptom | Likely cause |
|---------|----------------|
| App reappears after delete | OwnerReference — **Observed** `argo-advanced-stage` |
| No apps | Invalid template project/destination |
| Wrong count | Generator params / git path globs |
| Sync errors on child | [`argo-sync-failure.md`](./argo-sync-failure.md) |

## Diagnosis

1. Validate template `metadata.name` pattern — collisions prevent create.
2. Confirm **destination** namespace allowed in AppProject.
3. Cluster generator: lab uses **in-cluster only** — no remote cluster Secrets in milestone.
4. App-of-ApplicationSets: ensure parent Application synced first (waves).

## Safe Remediation

1. Fix ApplicationSet YAML in Git under `gitops/appsets/` → push → sync bootstrap Application.  
   **WARNING — SAFE MUTATION.**

2. To remove generated Application permanently: remove entry from generator or delete ApplicationSet (lab only).  
   **WARNING — DESTRUCTIVE** in lab — may prune child resources per sync policy.

3. **WARNING — SAFE MUTATION:** Temporary disable: scale applicationset controller — **Not tested**; avoid on shared Argo.

## Verification

- Expected Application count matches generator.
- Each child **Synced/Healthy** or documented demo state.
- Re-delete test: owner recreates — **Observed** behavior confirmed.

## Rollback

- Git revert ApplicationSet manifest — [`git-rollback.md`](./git-rollback.md).
- Re-apply from [`git-argo-recovery.md`](./git-argo-recovery.md) ApplicationSet section.

## Escalation

- AppProject denies template destination — [`argocd-appproject-denied.md`](./argocd-appproject-denied.md).
- Controller pod crash loop — Argo CD namespace health.

## Do Not Do

- Edit generated Application spec manually without changing template (drift + overwrite).
- Broad `*` destinations in ApplicationSet template on production.
- Register untrusted cluster Secrets for generators.

## Expected Recovery

Minutes after Git fix + ApplicationSet reconcile.

## Observed Project 1 Result

| Experiment | Status |
|------------|--------|
| Manual delete → regeneration | **Observed** |
| List generator stable names | **Observed** design |
| Git generator overlap experiments | **Design guidance** — review paths |

## Postmortem Notes

- Document generator type and whether delete was intentional test.
- Keep templates code-reviewed like Terraform modules.
