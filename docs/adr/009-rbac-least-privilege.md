# ADR 009: RBAC least privilege

- **Status:** Accepted

## Decision

Dedicated ServiceAccounts, least-privilege Roles/RoleBindings, Pod Security baseline, NetworkPolicy where enforced. `platform-lab` SA with `automountServiceAccountToken: false` observed.

## Evidence

Section 22 [security-rbac.md](../security-rbac.md) · [rbac-access-denied.md](../runbooks/rbac-access-denied.md) · [pod-security-admission.md](../runbooks/pod-security-admission.md)

Do not grant `cluster-admin` to debug.
