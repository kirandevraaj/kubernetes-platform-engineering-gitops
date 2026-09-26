# Security Incident (Platform)

## Workflow
Identify → Contain → Preserve evidence → Assess → Remediate → Rotate credentials → Verify → Document

## Example triggers
Unexpected RBAC access; Secret access; privileged Pod; NetworkPolicy change; unknown image digest.

## First 60 Seconds
1. Scope blast radius (ns / cluster / AWS account).  
2. **Evidence** without Secret values ([incident-evidence.md](../operations/incident-evidence.md)).  
3. Contain: isolate SA bindings / NetworkPolicy via Git if possible — avoid panic deletes.  

## Safe Remediation
Least-privilege Git fixes; rotate exposed credentials **out of band** (never commit). Re-verify PSA/RBAC.

## Escalation
Confirmed credential leak, privilege escalation, or data exfil → escalate immediately ([escalation.md](../operations/escalation.md)).

## Do Not Do
Paste tokens; grant cluster-admin “temporarily” without ticket; destroy evidence Pods before logs captured.

## Related
[rbac-access-denied.md](./rbac-access-denied.md) · [pod-security-admission.md](./pod-security-admission.md)
