# automation-lab-reader RBAC

ServiceAccount `automation-lab-reader` has get/list/watch only.
Attempting create/update/delete with this SA should return HTTP 403 Forbidden.

Apply against namespace `automation-lab` only:

```bash
kubectl apply -f examples/rbac/ -n automation-lab
```
