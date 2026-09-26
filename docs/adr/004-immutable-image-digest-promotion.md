# ADR 004: Immutable image digest promotion

- **Status:** Accepted

## Context

Tags are mutable references; environments must run the same verified artifact.

## Decision

Promote by **image digest**. Known-good:

`kirandevraaj/platform-lab:0.1.4` @ `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

Same digest on VMware and AWS overlays.

## Consequences

Rollback = Git pin to known digest + Argo reconcile (not primary `kubectl rollout undo`).

## Evidence

Commit `5da676f` · failed `0.1.5` rollback to `0.1.4` · [git-rollback.md](../runbooks/git-rollback.md)
