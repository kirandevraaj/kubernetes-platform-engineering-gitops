# Argo CD AppProject Denied Runbook (Project 1 — Section 26)

**Scope:** Application **InvalidSpecError** or sync denied — destination, repo, or resource kind violates AppProject.  
**Canonical lab example:** destination **kube-system** denied by `platform-advanced-lab` — [`argo-advanced-patterns.md`](../argo-advanced-patterns.md) § experiments.

---

## Symptoms

- Application status: `Unable to validate application: application destination spec is invalid`.
- Message contains **does not match any of the allowed destinations** in project `platform-advanced-lab`.
- Sync never starts; compare may still run.

## Impact

- Workloads in forbidden namespace/cluster **not** deployed — security control working as intended.
- Misconfigured production Application blocks entire release.

## Severity

| Context | Severity |
|---------|----------|
| Intentional security demo | **SEV-4** |
| Accidental prod app mis-projected | **SEV-2** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get application <app> -n argocd -o yaml | Select-String -Pattern project,destination,message`
2. **READ-ONLY:** `kubectl get appproject <project> -n argocd -o yaml`

## Preconditions

- AppProject allowlists live in Git (`gitops/projects/`). UI-only project edits are **not** SoT — export to Git per Section 25 gap report.

## Evidence

Compare Application `spec.destination` vs AppProject `spec.destinations` (namespace + server/name).

**Observed (Project 1):**

| Attempt | Result |
|---------|--------|
| Application targeting **kube-system** under `platform-advanced-lab` | **InvalidSpecError** — destination not allowlisted |

Allowed lab destinations include explicit namespaces (`argo-advanced-*`, `argocd`, etc.) — not `kube-system`.

## Triage

| Mismatch | Fix direction |
|----------|----------------|
| Wrong namespace | Change Application destination to allowed NS **or** update AppProject in Git (review) |
| Wrong repo URL | Align `source.repoURL` with `sourceRepos` |
| Disallowed kind | Adjust `namespaceResourceWhitelist` / cluster resources |

## Diagnosis

1. Confirm Application `spec.project` field — default project is permissive; lab production apps use dedicated projects (`platform-lab`, etc.).
2. **App-of-Apps** children still bound to same project — cannot bypass with nesting.
3. ApplicationSet template `project` must match allowlists.

## Safe Remediation

1. **Preferred:** Fix Application manifest destination to approved namespace (e.g. `argo-advanced-lab`).  
   **WARNING — SAFE MUTATION:** Git commit + sync.

2. **Expanding allowlist:** Add destination to AppProject in Git only after security review — **never** add `kube-system` casually.

3. Wrong project assignment: change `spec.project` to correct AppProject file in `gitops/projects/`.

## Verification

- Application validates; sync proceeds.
- Resources created only in allowed namespace.
- Argo RBAC still restricts who can sync.

## Rollback

- Revert AppProject or Application change via Git — [`git-rollback.md`](./git-rollback.md).

## Escalation

- Need system namespace deploy: platform architect + break-glass project — **Design guidance**, not lab-tested on prod.

## Do Not Do

- Set `project: default` on production apps to bypass restrictions.
- Allow `*` destinations in multi-tenant Argo.
- Deploy cluster-scoped resources without clusterResourceWhitelist review.

## Expected Recovery

Immediate after valid spec applied and Application reconciled.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| kube-system denied | **Observed** |
| Fix by moving to lab namespace | **Design guidance** |

## Postmortem Notes

- Was denial intentional test or mis-copy paste in template?
- ApplicationSet templates need same destination audit as single Applications.
