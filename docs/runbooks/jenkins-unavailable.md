# Jenkins Unavailable

## Impact
- Running Kubernetes workloads do **not** disappear because Jenkins is down.  
- Git desired state remains; Argo continues reconciliation.  
- **New CI releases** may be blocked.

## Recovery
Restore Jenkins → verify credentials (do not log) → verify agents → safe validation build if needed.

## Related
[jenkins-build-failure.md](./jenkins-build-failure.md) · [github-unavailable.md](./github-unavailable.md)
