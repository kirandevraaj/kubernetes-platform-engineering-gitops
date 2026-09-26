# Docker / Registry Release Failure

## Principles
- **Tag** = mutable reference  
- **Digest** = immutable artifact identity  
- Known-good: `0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

## Symptoms
Version collision; build failure; push failure; digest missing; GitOps promotion refused.

## First 60 Seconds
Inspect Jenkins stage logs; confirm version file / tag policy; do not overwrite unknown digests.

## Safe Remediation
Bump version per project rules; rebuild; capture digest; promote via Git. Never “force” a known-bad digest into production overlays.

## Verification
Digest in GitOps matches `docker inspect` / registry; Argo shows correct image; pods Running Ready.

## Related
[jenkins-build-failure.md](./jenkins-build-failure.md) · [registry-unavailable.md](./registry-unavailable.md) · [git-rollback.md](./git-rollback.md)
