# AWS ALB Unhealthy Targets Runbook (Project 1 — Section 26)

**Scope:** AWS EKS — Application Load Balancer target group **unhealthy** for `platform-lab` Ingress.  
**Lab traits:** `target-type: ip`, health check path **`/health`**, namespace `platform-lab`.  
**VMware:** use [`metallb-vip-failure.md`](./metallb-vip-failure.md) / [`ingress-unavailable.md`](./ingress-unavailable.md) instead.

---

## Symptoms

- AWS console/CLI: targets **unhealthy** or **draining**.
- Public ALB URL returns 502/503.
- Ingress shows ADDRESS with ALB hostname; pods may be Running.

## Impact

- North-south traffic dropped for AWS overlay despite in-cluster Service working.
- Autoscaling may add NotReady pods that fail health checks.

## Severity

| Healthy target count | Severity |
|---------------------|----------|
| ≥1 healthy | **SEV-3** |
| 0 healthy | **SEV-1** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get pods,ingress -n platform-lab -o wide`
2. **READ-ONLY:** `kubectl get endpoints -n platform-lab`
3. **READ-ONLY:** `kubectl describe ingress platform-lab -n platform-lab` (controller events)
4. From pod network or exec: `curl -s -o NUL -w "%{http_code}" localhost:8000/health` (**READ-ONLY**)

AWS CLI (READ-ONLY — replace ARN from your account/console; do not commit account-specific secrets):

```powershell
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

## Preconditions

- AWS Load Balancer Controller running in cluster — **Design guidance**.
- Security groups allow ALB → pod ENI paths — Terraform/VPC docs.

## Evidence

- Target health reason codes (`Target.FailedHealthChecks`, `Target.Timeout`).
- Pod readiness probe results.
- Image digest on AWS overlay vs known-good `…872ff`.

## Triage

| Reason | Runbook |
|--------|---------|
| Pod NotReady | [`pod-not-ready.md`](./pod-not-ready.md) |
| No endpoints | [`service-endpoint-troubleshooting.md`](./service-endpoint-troubleshooting.md) |
| Wrong health path/port | Git Ingress/Service fix |
| Bad release | [`git-rollback.md`](./git-rollback.md) |

## Diagnosis

1. ALB checks **`/health`** on pod IP — must match app listen port **8000** Service target.
2. **Observed:** Same digest as VMware can stay **Ready** on AWS when VMware-only fault injected (`APP_ENVIRONMENT=aws-eks-gitops`) — rollout lab.
3. NetworkPolicy objects exist on AWS but **enforcement not observed** in lab — unlikely ALB block via NP; verify SGs first.

## Safe Remediation

1. Fix readiness/app in Git → Argo sync `platform-lab-aws` (**SAFE MUTATION**).
2. Wait for target registration after pod Ready (READ-ONLY poll).
3. **WARNING — SAFE MUTATION:** Delete failing pod to recreate if crash — Deployment only.

## Verification

- All targets **healthy** in target group.
- HTTP 200 on ALB URL `/health` and `/version` **0.1.4** when on known-good digest.

## Rollback

- **Git revert** digest on `kubernetes/overlays/aws` — primary; not `kubectl rollout undo`.

## Escalation

- Controller errors — AWS API [`aws-api-failure.md`](./aws-api-failure.md).
- Repeated unhealthy with Ready pods — SG/subnet routing review (**Design guidance**).

## Do Not Do

- Disable health checks in production to go green.
- Switch to instance target mode without Git review (lab uses **ip**).

## Expected Recovery

Minutes after pods Ready and targets re-register.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| `/health` path on ALB | **Design guidance** from overlay |
| Healthy targets during VMware-only bad release | **Observed** env gating |
| Full ALB outage drill | **Not tested** |

## Postmortem Notes

- Capture target reason code and pod readiness timeline.
- Confirm promotion did not skip AWS overlay validation.
