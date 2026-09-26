# Service Endpoint Troubleshooting Runbook (Project 1 — Section 26)

**Scope:** Kubernetes **Service** has no or wrong **Endpoints** / EndpointSlice — traffic blackholed inside cluster and at ingress/ALB.  
**Lab app:** Service `platform-lab` port **8000**, selector labels on Deployment pods.

---

## Symptoms

- `kubectl get endpoints platform-lab -n platform-lab` — **empty subsets** or missing pod IPs.
- Ingress/ALB 502 while pods exist.
- `curl` from debug pod to Service ClusterIP fails.

## Impact

- Load balancers only forward to **Ready** endpoints.
- **Observed:** During bad rollout, endpoints count **2** (old Ready only) while surge pod excluded.

## Severity

**SEV-2** when production path shows 502; **SEV-3** during controlled rollout with surviving endpoints.

## First 60 Seconds

1. **READ-ONLY:** `kubectl get svc,endpoints -n platform-lab`
2. **READ-ONLY:** `kubectl get pods -n platform-lab -l app.kubernetes.io/name=platform-lab -o wide`
3. **READ-ONLY:** Compare Service `spec.selector` vs pod labels.

## Preconditions

- Understand readiness gates Endpoints — NotReady pods excluded automatically.

## Evidence

```powershell
kubectl get svc platform-lab -n platform-lab -o yaml
kubectl get endpoints platform-lab -n platform-lab -o yaml
kubectl get pods -n platform-lab --show-labels
```

## Triage

| Endpoints | Cause |
|-----------|-------|
| Empty, no pods | Deployment scaled to 0 or label mismatch |
| Empty, pods Running not Ready | [`pod-not-ready.md`](./pod-not-ready.md) |
| Partial IPs | Rolling update / maxUnavailable |
| IPs present, ingress fails | [`ingress-unavailable.md`](./ingress-unavailable.md) |

## Diagnosis

1. **Label drift:** Service selector not matching template labels — Git overlay check.
2. **Named ports:** Ingress backend port name must match Service port name.
3. **Headless vs ClusterIP:** lab uses ClusterIP.
4. **AWS ALB IP mode:** registers pod IPs directly — endpoints must be current.

## Safe Remediation

1. Fix labels/selector in Git → Argo sync (**SAFE MUTATION**).
2. Fix readiness → endpoints repopulate automatically.
3. **WARNING — SAFE MUTATION:** Accidental selector change — revert Git, not manual Service patch on prod apps.

## Verification

- EndpointSlice addresses count = Ready pods.
- In-cluster: `kubectl run curl-test --rm -it --image=curlimages/curl -- curl -s http://platform-lab.platform-lab.svc:8000/health` (**Design guidance** — remove test pod after).

## Rollback

- Git revert — [`git-rollback.md`](./git-rollback.md).

## Escalation

- NetworkPolicy blocking ingress controller → app on VMware — [`networkpolicy-troubleshooting.md`](./networkpolicy-troubleshooting.md).

## Do Not Do

- Manually edit Endpoints (legacy) — controller owns them.
- Assume Endpoints include NotReady pods.

## Expected Recovery

Immediate when pods transition to Ready.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| 2 endpoints during stuck rollout | **Observed** VMware 0.1.5 |
| Endpoints exclude NotReady surge | **Observed** Kubernetes behavior |

## Postmortem Notes

- Snapshot Endpoints YAML during incident.
- Verify selector changes in PR review.
