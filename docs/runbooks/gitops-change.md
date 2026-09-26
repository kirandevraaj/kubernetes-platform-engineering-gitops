# GitOps Change Runbook (Project 1 — Section 26)

**Scope:** Safe procedure to introduce **desired state** changes via Git → Argo CD — promotions, overlays, platform config.  
**Repository:** `https://github.com/kirandevraaj/kubernetes-platform-engineering-gitops.git` (no credentials here).  
**Related:** [`git-rollback.md`](./git-rollback.md), [`failed-rollout.md`](./failed-rollout.md), [`git-argo-recovery.md`](./git-argo-recovery.md).

---

## Symptoms

*(This runbook is proactive — use when planning a change, not when broken.)*

- Need to promote image digest, scale replicas, update Ingress, or add manifest.
- CI (Jenkins) updated tag/digest on overlay branch/`main`.

## Impact

- Incorrect change affects **both** clusters if shared path; overlays **local** vs **aws** isolate most app config.
- Argo poll delay before sync — plan maintenance communication.

## Severity

Classify change: **standard** (ConfigMap text) vs **release** (digest) vs **breaking** (CRD/API).

## First 60 Seconds (pre-change)

1. **READ-ONLY:** Current Argo revision and health: `kubectl get application -n argocd`
2. **READ-ONLY:** Known-good digest for rollback: `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` (**0.1.4**)
3. Identify target paths: `kubernetes/overlays/local`, `kubernetes/overlays/aws`, `gitops/applications/`.

## Preconditions

- Change authored in Git — not kubectl edit for production-like apps.
- PR review for AppProject boundaries and sync options.
- CI contract: Jenkins builds image; Git records digest — **Observed** pattern; local Docker build used in rollout lab **Observed**.

## Evidence (before)

- Export `kubectl get deploy -n platform-lab -o jsonpath='{.items[0].spec.template.spec.containers[0].image}'`
- HTTP `/version` at VIP and ALB.
- Argo app sync revision SHA.

## Triage (change type)

| Type | Path | Risk |
|------|------|------|
| Digest promotion | overlay kustomization/image patch | Readiness gate — see 0.1.5 lab |
| Replicas/HPA | overlay | HPA may fight if not ignored |
| Advanced demo | `argo-advanced-*` | Isolated project |
| Infra | Terraform | Not Argo — separate runbook |

## Diagnosis (readiness)

- Will new image pass `/health` on **each** overlay env var (`local-gitops` vs `aws-eks-gitops`)?
- RollingUpdate params: `maxUnavailable: 0` preserves service during bad surge **Observed**.

## Safe Remediation (execution steps)

1. Implement change in feature branch; `kustomize build` locally if available (**READ-ONLY** validate).
2. Merge to `main` (**WARNING — SAFE MUTATION** on Git).
3. Wait or trigger Argo refresh on target Application (`platform-lab-local`, `platform-lab-aws`).
4. **READ-ONLY** watch: `kubectl rollout status`, endpoints, `/health`.
5. If advanced hooks/waves: confirm order in UI — [`argo-advanced-patterns.md`](../argo-advanced-patterns.md).

**Do not** rely on `kubectl set image` without immediate Git follow-up (selfHeal drift).

## Verification

- Argo **Synced / Healthy** (or expected Progressing during rollout).
- Digest matches promotion commit.
- Observability: deployment available replicas — optional Grafana **Design guidance**.

## Rollback

- [`git-rollback.md`](./git-rollback.md) — revert commits; **Observed ~6s** VMware reconcile after 0.1.4 restore.
- Not primary: `kubectl rollout undo`.

## Escalation

- Sync failure — [`argo-sync-failure.md`](./argo-sync-failure.md).
- Bad merge on `main` — platform owner revert rights.

## Do Not Do

- Commit Secrets, kubeconfigs, or tokens.
- Enable Replace/Force on production Applications.
- Promote intentional fault digests without env gating lesson scope.

## Expected Recovery

N/A for forward change; failed change recovery via Git rollback minutes or less **Observed**.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Digest promotion 0.1.5 + env-gated fault | **Observed** |
| Dual overlay same digest different readiness | **Observed** |
| Jenkins UI end-to-end in rollout lab | **Not tested** |

## Postmortem Notes

- Link PR, commits, digests, and cluster contexts validated.
- Note whether AWS and VMware were both synced.
