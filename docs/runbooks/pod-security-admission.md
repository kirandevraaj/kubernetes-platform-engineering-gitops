# Pod Security Admission

## Observed Project 1
| Environment | Baseline label |
|---|---|
| VMware | `baseline:v1.31` |
| AWS | `baseline:v1.36` |

Under baseline, **root user** may produce **warnings** (observed) without necessarily blocking.

## Symptoms
Admission denied/warned for privileged, hostNetwork, hostPID, hostPath, etc.

## First 60 Seconds (READ-ONLY)
```bash
kubectl get ns platform-lab --show-labels
kubectl get events -n platform-lab --field-selector reason=FailedCreate
kubectl describe pod -n platform-lab <pod>
```

## Diagnosis
Compare PodSecurity namespace labels (`enforce`/`audit`/`warn`) to Pod spec. Privileged / host* / hostPath typically violate baseline/restricted.

## Safe Remediation
Adjust workload securityContext in Git to comply; do not weaken cluster PSA to “make it work” without review.

## Related
[security-rbac.md](../security-rbac.md) · [security-incident.md](./security-incident.md)
