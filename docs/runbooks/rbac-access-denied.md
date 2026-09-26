# RBAC Access Denied

**Observed in Project 1:** Section 22 security-lab findings. Prefer diagnose before grant.

## Symptoms
`Forbidden`, `cannot list resource`, UI/API 403.

## First 60 Seconds (READ-ONLY)
```bash
kubectl auth can-i list pods -n platform-lab --as=system:serviceaccount:platform-lab:platform-lab
kubectl auth can-i --list -n platform-lab --as=system:serviceaccount:platform-lab:platform-lab
kubectl get role,rolebinding,clusterrole,clusterrolebinding -n platform-lab
```

## Triage flow
1. **Who?** user / ServiceAccount  
2. **What?** verb + resource + subresource  
3. **Where?** namespace vs cluster  
4. **Which Role/ClusterRole?**  
5. **Which Binding?**

## Safe Remediation
Grant least privilege via Git (security-lab patterns). Do **not** bind `cluster-admin` to debug.

## Verification
`kubectl auth can-i` returns `yes` for intended verb only; unintended verbs still `no`.

## Related
[serviceaccount-troubleshooting.md](./serviceaccount-troubleshooting.md) · [security-rbac.md](../security-rbac.md)
