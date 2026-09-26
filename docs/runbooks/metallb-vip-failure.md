# MetalLB VIP Failure Runbook (Project 1 — Section 26)

**Scope:** VMware only — MetalLB **L2** pool `lab-pool` **`192.168.56.200`–`192.168.56.210`**, ingress-nginx LoadBalancer Service.  
**Not applicable:** AWS (uses ALB) — see [`aws-alb-unhealthy.md`](./aws-alb-unhealthy.md).

---

## Symptoms

- `kubectl get svc -n ingress-nginx` — EXTERNAL-IP **pending** or wrong IP.
- VIP `192.168.56.200` unreachable from workstation.
- ARP/L2 flapping or duplicate IP (rare).

## Impact

- No north-south HTTP to `platform-lab.local` despite healthy app pods.
- Observability Grafana LB on MetalLB (if enabled) also affected.

## Severity

**SEV-1** for lab external access until VIP restored.

## First 60 Seconds

1. **READ-ONLY:** `kubectl get svc -n ingress-nginx`
2. **READ-ONLY:** `kubectl get pods -n metallb-system -o wide`
3. **READ-ONLY:** `kubectl get ipaddresspool,l2advertisement -n metallb-system`
4. Ping/curl `192.168.56.200` from workstation (READ-ONLY).

## Preconditions

- Cluster CNI Calico; MetalLB v0.16.1 **Design guidance** from architecture docs.
- Host-only network `192.168.56.0/24` reachable from operator machine.

## Evidence

```powershell
kubectl describe svc ingress-nginx-controller -n ingress-nginx
kubectl logs -n metallb-system -l app.kubernetes.io/component=speaker --tail=50
kubectl get events -n metallb-system --sort-by='.lastTimestamp'
```

## Triage

| Finding | Direction |
|---------|-----------|
| Speaker pods not Running | Node taints, image pull |
| Pool exhausted | Assign unused IP in range |
| Service not LoadBalancer | Git/Helm regression |
| Controller has endpoints 0 | [`ingress-unavailable.md`](./ingress-unavailable.md) |

## Diagnosis

1. Confirm **one** Service claims `.200` (ingress controller).
2. Speaker must run on node that can advertise L2 on lab LAN.
3. Worker node loss may remove speaker or controller — correlate with [`worker-node-failure.md`](./worker-node-failure.md).

## Safe Remediation

1. Restore MetalLB controller/speaker pods (**WARNING — SAFE MUTATION:** delete stuck pod to recreate — lab only).
2. Fix Service type and annotations in Git → Argo/Helm sync — **preferred**.
3. **WARNING — SAFE MUTATION:** Adjust IPAddressPool only via Git manifests — avoid ad hoc IP collisions.

## Verification

- Service EXTERNAL-IP = `192.168.56.200` (or intended pool member).
- `curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health` → 200.

## Rollback

- Git revert MetalLB or ingress Service changes → sync.

## Escalation

- Hypervisor networking / VMware host-only misconfiguration.
- Calico BGP conflicts — **Not tested** in this lab (L2 mode).

## Do Not Do

- Assign `.200` on hypervisor host OS manually.
- Deploy MetalLB on AWS EKS for this project pattern.

## Expected Recovery

Minutes after speaker + Service healthy.

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Stable VIP .200 for ingress | **Observed** baseline inventory |
| VIP failure root-cause drill | **Design guidance** — use speaker logs |

## Postmortem Notes

- Document whether VIP or backend caused outage.
- Pool utilization (200–210) for future LBs.
