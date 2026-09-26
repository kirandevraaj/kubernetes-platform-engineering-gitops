# ServiceAccount Troubleshooting

## Observed Project 1
`platform-lab` uses a **dedicated** ServiceAccount with **`automountServiceAccountToken: false`**.

## Symptoms
Wrong identity; unexpected token mount; RBAC denials; Pod fails projecting token.

## First 60 Seconds (READ-ONLY)
```bash
kubectl get sa -n platform-lab
kubectl get pod -n platform-lab -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.serviceAccountName}{"\n"}{end}'
kubectl describe sa -n platform-lab platform-lab
```

## Diagnosis
- Pod `serviceAccountName` matches Git desired state?
- `automountServiceAccountToken` intentional?
- Token volume projected when needed for in-cluster clients?

## Safe Remediation
Fix via GitOps manifests. Do not paste tokens into tickets.

## Related
[rbac-access-denied.md](./rbac-access-denied.md) · [pod-security-admission.md](./pod-security-admission.md)
