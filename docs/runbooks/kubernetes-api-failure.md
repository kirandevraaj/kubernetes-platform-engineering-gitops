# Runbook: Kubernetes API Failure (Project 1)

**Scope:** Kubernetes Python client / kubectl against `ckad-lab` or EKS.  
**Safe mutate:** `automation-lab` · **GitOps apps:** fix via Git + Argo, not imperative overrides on `platform-lab`.

---

## Symptoms

- `ApiException` 401/403/404/409/429/5xx  
- Wrong cluster objects listed  
- Watch/list hang  
- Verify UNKNOWN (not Ready in time)  
- Argo Healthy but automation still fails (different namespace/context)

---

## Checks

```powershell
kubectl config get-contexts
kubectl config current-context
kubectl cluster-info
kubectl get ns
kubectl -n automation-lab get deploy,svc,pods
kubectl -n automation-lab get events --sort-by=.lastTimestamp
```

Python pin check: `pip show kubernetes` → `32.0.1`.

---

## Common failures

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Wrong context | Unexpected nodes/namespaces | `use-context ckad-lab` or AWS tools context |
| 401 auth | Unauthorized | Fix kubeconfig/exec auth; refresh EKS token |
| 403 RBAC | Forbidden | Grant least-privilege Role—do not jump to cluster-admin |
| 404 | Wrong name/NS | Confirm `automation-lab`; create NS only if lab-approved |
| 409 conflict | Concurrent write | Re-get; patch; limited retry |
| 429 / apiserver overload | Too many requests | Backoff; reduce concurrency |
| Timeout / not Ready | verify UNKNOWN | Inspect pods/events; fix image/pull/limits; then re-verify |
| Client skew myths | odd decode errors | Stay on `32.0.1`; Core/Apps still OK on 1.36 |

---

## GitOps interaction

- If `platform-lab` drifts: **Argo self-heal / sync from Git**—do not forever kubectl-patch.  
- If automation fights Argo on the same object: stop automation; choose one owner.  
- Image digest issues: confirm Git still pins `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` for this milestone.

---

## Recovery

1. Correct context and RBAC.  
2. Read-only get/list succeeds.  
3. Plan/apply only `automation-lab`.  
4. Wait with timeout; classify UNKNOWN vs FAIL.  
5. Re-run idempotent ensure.

---

## Related

[automation-failure](./automation-failure.md) · [argo-gitops-reference](../architecture/argo-gitops-reference.md)
