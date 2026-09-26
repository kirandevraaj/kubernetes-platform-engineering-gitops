# Argo CD Sync Failure Runbook (Project 1 — Section 26)

**Scope:** Sync **Error**, **Failed** operation, **ComparisonError**, render failures, admission denials.  
**Related:** [`argo-outofsync.md`](./argo-outofsync.md), [`argocd-appproject-denied.md`](./argocd-appproject-denied.md), [`argo-advanced-patterns.md`](../argo-advanced-patterns.md).

---

## Symptoms

- Application `status.operationState.phase: Failed` or sync stuck retrying.
- Messages: **ComparisonError**, **InvalidSpecError**, **permission denied**, **kustomize build failed**.
- UI: red sync error; resources partially applied.

## Impact

- Desired Git state **not** fully applied — partial sync can leave broken dependencies.
- Health checks may lie if only subset of manifests applied.
- Advanced lab demos can fail without affecting `platform-lab-local` / `platform-lab-aws` if isolated.

## Severity

| Scope | Severity |
|-------|----------|
| Disposable advanced app only | **SEV-4** |
| Production-like app sync failed | **SEV-2** |
| Argo CD itself cannot fetch Git | **SEV-1** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get application <app> -n argocd -o yaml | Select-String -Pattern message,phase,conditions -Context 0,2`
2. Note **project**, **source.path**, **targetRevision**.
3. **READ-ONLY:** `kubectl get events -n argocd --sort-by='.lastTimestamp' | Select-Object -Last 20`

## Preconditions

- Repo URL is public HTTPS in docs — credentials stay in cluster Secrets only; **never** log Secret data.
- For Kustomize paths, validate from workstation with `kustomize build` (READ-ONLY local) if tool installed.

## Evidence

Capture full `status.operationState.message`, sync wave/hook failures, and failing resource name.

**Lab note (Design guidance / troubleshooting):** Health-gated demo Application `argo-waves-health-demo` path `kubernetes/argo-advanced-lab/waves-health`. A **ComparisonError** referencing missing `../base/namespace.yaml` indicates a **broken Kustomize reference** (file moved or wrong `resources` entry). Current repo `waves-health/kustomization.yaml` lists only `resources.yaml` — if error persists, compare Application path to on-disk kustomization and fix in Git.

## Triage

| Error class | Runbook |
|-------------|---------|
| AppProject destination/kind | [`argocd-appproject-denied.md`](./argocd-appproject-denied.md) |
| Git fetch / ComparisonError | Network, repo access, manifest path |
| Hook Job failed | [`argo-advanced-patterns.md`](../argo-advanced-patterns.md) SyncFail demo |
| Sync window blocked | Clear windows in Git after lab (`syncWindows: []`) |
| SSA/conflict | Advanced sync options — lab only |

## Diagnosis

1. Reproduce manifest render: path + revision from Application spec.
2. **Observed:** AppProject **kube-system** destination denied — `InvalidSpecError` for `platform-advanced-lab`.
3. **Observed:** Combined hooks order Namespace → PreSync → … — success path documented in advanced patterns.
4. Check CRD ordering (waves) — CRD must exist before CR.

## Safe Remediation

1. Fix manifest or AppProject in **Git**; push; retry sync.  
   **WARNING — SAFE MUTATION:** Git commit.

2. **WARNING — SAFE MUTATION:** Retry sync from UI/CLI after fix — may apply partial remaining resources.

3. If sync left orphan hook Jobs: delete failed hook Jobs in **lab namespaces only** (**WARNING — SAFE MUTATION**).

4. GitHub outage: wait or use cached repo on Argo repo-server — [`git-argo-recovery.md`](./git-argo-recovery.md).

Do not enable **Replace** on production apps to “force through”.

## Verification

- Application **Synced** and **Healthy** (or expected Progressing for demos).
- `kubectl get all -n <target-ns>` matches intent.
- No failing operation in `status.operationState`.

## Rollback

- Revert breaking Git commit → sync — [`git-rollback.md`](./git-rollback.md).
- Partial apply: fix forward in Git; avoid manual orphan deletes in production namespaces without inventory.

## Escalation

- Argo CD control plane down — [`kubernetes-api-failure.md`](./kubernetes-api-failure.md).
- Persistent ComparisonError on `main` — platform GitOps owner.

## Do Not Do

- Paste repo credentials into runbook tickets or commits.
- Point production Application at experimental path without AppProject review.
- `--force` sync production workloads.

## Expected Recovery

| Fix type | RTO |
|----------|-----|
| Kustomize path fix + sync | minutes |
| AppProject allowlist fix | minutes after Git merge |

## Observed Project 1 Result

| Item | Status |
|------|--------|
| kube-system destination denied | **Observed** advanced lab |
| SyncFail hook demo Failed phase | **Observed** — main apps unaffected |
| waves-health ComparisonError (bad base ref) | **Design guidance** — fix Kustomize paths in Git |

## Postmortem Notes

- Include Application name, path, revision, and exact API error string.
- Add CI kustomize build for changed paths.
