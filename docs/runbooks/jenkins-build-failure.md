# Jenkins Build Failure

## Pipeline stages (Project 1)
Checkout → Change detection → Test → Read version → Build → Validate → Push → Digest capture → GitOps promotion.

## Symptoms
Red build; skipped stages unexpectedly; push/digest/promote failure.

## First 60 Seconds (READ-ONLY)
- Open failing build console (no credentials in paste).
- Identify stage name.
- Confirm whether change was **app** (full CI) or **GitOps-only** (CI stages skipped by design — loop prevention).

## Diagnosis
| Stage | Typical cause |
|---|---|
| Checkout | Git/ creds / ref |
| Test | unit failure |
| Build | Dockerfile / daemon |
| Push | registry auth / network |
| Digest | inspect failure |
| Promote | Git push / conflict / refuse rules |

## Safe Remediation
Fix source in Git; re-run pipeline. Do not manually edit cluster to “match” a failed promote.

## Verification
Build green; digest in Git matches registry; Argo Synced/Healthy; `/health` 200.

## Related
[docker-release-failure.md](./docker-release-failure.md) · [gitops-change.md](./gitops-change.md) · [jenkins-unavailable.md](./jenkins-unavailable.md)
