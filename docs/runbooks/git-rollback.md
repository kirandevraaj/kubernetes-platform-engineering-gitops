# Git Rollback Runbook (Project 1 — Section 26)

**Scope:** Revert **bad desired state** on Git `main` and let Argo CD reconcile — primary GitOps rollback for Project 1.  
**Reference incident:** VMware `0.1.5` readiness failure → Git restore **`0.1.4`** digest — [`vmware-rollout-failure-rollback.md`](../vmware-rollout-failure-rollback.md).  
**Section 25 companion:** [`git-argo-recovery.md`](./git-argo-recovery.md) (DR narrative — do not overwrite).

---

## Symptoms

- Bad merge/promotion: app misbehaves, stuck rollout, wrong config synced.
- Argo **Synced** to bad revision; health **Degraded**.
- Need authoritative return to last known-good Git state.

## Impact

- Restores **configuration** RPO ≈ 0 for Git-tracked objects **Design guidance** from DR docs.
- Does **not** restore EBS file contents or ephemeral data.

## Severity

**SEV-2** until reverted for production-like apps; **SEV-3** for disposable `dr-lab`.

## First 60 Seconds

1. **READ-ONLY:** Identify last good commit SHA on `main` (Git log).
2. **READ-ONLY:** `kubectl get application <app> -n argocd` — current `status.sync.revision`
3. **READ-ONLY:** Confirm traffic impact: endpoints, `/health`
4. Stop further promotions until revert merged.

## Preconditions

- Known-good platform-lab digest:  
  `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`
- Write access to GitHub via normal org process — **no tokens in runbook**.

## Evidence

- Bad commits (lab): `0c4fe12`, `6acbe3e` (0.1.5 promote)
- Revert commits (lab): `302a506`, `95820c8`
- Argo revision after recovery: synced to restored overlay + app source

## Triage

| Situation | Action |
|-----------|--------|
| Bad image digest only | Revert overlay image patch |
| Bad app source (/health) | Revert `app/**` + overlay if needed |
| Bad Argo Application spec | Revert `gitops/applications/` |
| Live drift only | Sync/selfHeal — [`argo-outofsync.md`](./argo-outofsync.md) |

## Diagnosis

1. Confirm both **image** and **ConfigMap env** align (VMware 503 was env-gated **Observed**).
2. Separate Applications: revert **both** `platform-lab-local` and `platform-lab-aws` paths if shared mistake.
3. Argo may show **Progressing** until Deployment completes — not necessarily OutOfSync.

## Safe Remediation

1. `git revert` bad commit(s) on `main` **or** restore files to known-good digest/version (**WARNING — SAFE MUTATION** — Git).
2. Push to origin; verify GitHub shows expected SHA.
3. **READ-ONLY:** Refresh/wait Argo — hard refresh if needed (**WARNING — SAFE MUTATION** — triggers reconcile).
4. **READ-ONLY:** Watch rollout and endpoints.

**Secondary / break-glass only:** `kubectl rollout undo` — then immediately align Git or selfHeal reintroduces drift. **Not tested** as primary — **Design guidance**.

## Verification

- Deployment image `@sha256:1cca2b59…872ff` (full in Git).
- Ready replicas == desired; bad ReplicaSet scaled to 0 **Observed**.
- Argo **Synced / Healthy**.
- `/health` 200; `/version` **0.1.4** at edge.

## Rollback of the rollback

- Forward-fix with new commit if revert was wrong — prefer new commit over force-push **Design guidance**.

## Escalation

- GitHub down — local clone + cache on repo-server [`git-argo-recovery.md`](./git-argo-recovery.md).
- Argo cannot sync — [`argo-sync-failure.md`](./argo-sync-failure.md).

## Do Not Do

- Leave bad `/health` behavior on `main` “for demo”.
- Force-push `main` without team agreement.
- Delete production resources as “rollback”.

## Expected Recovery

**Observed ~6s** Argo reconcile + Deployment stable **2/2** VMware lab.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Git digest rollback restores service | **Observed** |
| Old RS serves during bad surge | **Observed** |
| kubectl rollout undo primary | **Not tested** — rejected pattern |

## Postmortem Notes

- Timeline: push T0 → Argo revision T1 → endpoints healthy T2.
- Add CI gate preventing ungated env faults on shared promote.
