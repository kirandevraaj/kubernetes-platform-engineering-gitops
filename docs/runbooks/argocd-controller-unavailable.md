# Argo CD Controller Unavailable

## Impact model (Design guidance / partial observation)
- Existing workloads may **continue running**.  
- Git desired state remains intact.  
- Reconciliation **pauses** until controller recovery.  

Do **not** intentionally kill the Argo controller to test this runbook.

## First 60 Seconds (READ-ONLY)
```bash
kubectl get pods -n argocd
kubectl get application -n argocd
kubectl get deploy -n argocd
```

## Recovery
1. Restore Argo components (GitOps/Helm/install path used by lab).  
2. Validate repo access.  
3. Validate Applications Synced/Healthy.  
4. Reconcile if needed.  
5. Verify app `/health`.

## Related
[argo-outofsync.md](./argo-outofsync.md) · [git-argo-recovery.md](./git-argo-recovery.md)
