# GitHub Unavailable

## Impact (do not claim untested detail)
- New Git changes cannot be pushed/read.  
- Existing Kubernetes desired state may continue running.  
- Argo behavior depends on cached/repository access — **Not fully characterized as a destructive drill in Project 1.**

## Recovery
Restore repository access → verify Argo source → verify Jenkins checkout → resume workflow.

## Related
[gitops-change.md](./gitops-change.md) · [git-argo-recovery.md](./git-argo-recovery.md)
