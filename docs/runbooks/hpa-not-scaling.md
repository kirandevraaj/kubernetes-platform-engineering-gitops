# HPA Not Scaling

**Labels:** Observed in Project 1 (VMware 2→4; AWS 2→3 under CPU load). Timing not guaranteed.

## Symptoms
HPA `currentReplicas` stuck; `kubectl top` fails or shows low CPU; Events mention `FailedGetResourceMetric`.

## Impact / Severity
Degraded capacity under load — typically SEV-3 unless traffic loss (SEV-2).

## First 60 Seconds (READ-ONLY)
```bash
kubectl config current-context
kubectl get hpa -n platform-lab -o wide
kubectl describe hpa -n platform-lab
kubectl top nodes
kubectl top pods -n platform-lab
kubectl get apiservice v1beta1.metrics.k8s.io
```

## Triage
1. Metrics Server healthy? → [metrics-server-unavailable.md](./metrics-server-unavailable.md)
2. Requests set on containers? HPA needs CPU/memory requests.
3. Utilization below target? Scale-up may be correct idle behavior.
4. Max replicas already reached?

## Diagnosis
- Compare `currentCPUUtilizationPercentage` vs target.
- Check Deployment replica count vs HPA status.
- Events: `SuccessfulRescale` vs metric fetch errors.

## Safe Remediation
- Fix Metrics Server / kubelet scrape (platform change via GitOps if durable).
- Ensure resource requests exist in Git desired state.
- Do **not** manually scale Deployment long-term while HPA owns replicas (Argo/HPA fight).

## Verification
HPA shows sensible current/desired; under load replicas increase (lab: VMware→4, AWS→3). Scale-down is slower — expected.

## Escalation
Metrics API broken cluster-wide; or HPA mutating wrong Deployment.

## Do Not Do
Force delete HPA; set replicas via `kubectl scale` as permanent fix; invent latency-based HPA without metrics.

## Observed Project 1 Result
CPU load experiments scaled VMware 2→4 and AWS 2→3. Exact seconds vary.

## Related
[golden-signals.md](../operations/golden-signals.md) · [metrics-server-unavailable.md](./metrics-server-unavailable.md)
