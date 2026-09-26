# Ingress Unavailable Runbook (Project 1 — Section 26)

**Scope:** External HTTP(S) unreachable via **ingress-nginx** — VMware MetalLB VIP vs AWS ALB.  
**VMware VIP:** `192.168.56.200` · Host `platform-lab.local`.  
**Related:** [`metallb-vip-failure.md`](./metallb-vip-failure.md), [`aws-alb-unhealthy.md`](./aws-alb-unhealthy.md), [`service-endpoint-troubleshooting.md`](./service-endpoint-troubleshooting.md).

---

## Symptoms

- `curl` to VIP/ALB times out or connection refused.
- Browser/API 502/503/504 from nginx or ALB.
- Kubernetes Ingress exists but no traffic path.

## Impact

- Total loss of north-south access even if app pods Ready.
- **Observed historical:** VMware **single** ingress replica on failed worker → **0 endpoints** while app had Ready pods.

## Severity

| Signal | Severity |
|--------|----------|
| Partial 502, some targets up | **SEV-2** |
| Complete timeout to VIP/ALB | **SEV-1** |

## First 60 Seconds

**VMware:**

```powershell
kubectl get pods -n ingress-nginx -o wide
kubectl get svc -n ingress-nginx
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health
```

**AWS:**

```powershell
kubectl get ingress -n platform-lab
kubectl get pods -n platform-lab -l app.kubernetes.io/name=platform-lab
# ALB health via AWS console/CLI READ-ONLY — target health
```

## Preconditions

- Workstation routes to `192.168.56.0/24` (VMware host-only) — [`business-continuity.md`](../business-continuity.md).
- DNS/hosts file maps `platform-lab.local` — no secrets in docs.

## Evidence

- Ingress controller Endpoints count.
- `kubectl describe ingress -n platform-lab`.
- Events in `ingress-nginx` and app namespace.

## Triage

| Layer | Check |
|-------|-------|
| MetalLB VIP | [`metallb-vip-failure.md`](./metallb-vip-failure.md) |
| Controller pods | Node failure, image pull |
| Backend Service | [`service-endpoint-troubleshooting.md`](./service-endpoint-troubleshooting.md) |
| AWS ALB targets | [`aws-alb-unhealthy.md`](./aws-alb-unhealthy.md) |
| NetworkPolicy (VMware) | [`networkpolicy-troubleshooting.md`](./networkpolicy-troubleshooting.md) |

## Diagnosis

### VMware

- Controller Service type **LoadBalancer** with MetalLB annotation/pool `lab-pool` `192.168.56.200-210`.
- **Observed:** **2/2** controller replicas with topology spread — post-HA; prior SPOF on worker-02 documented.
- App path: VIP → ingress-nginx → Service `platform-lab` → pods `:8000`.

### AWS

- Ingress class **alb**; targets **IP** mode; health check **`/health`**.
- Unhealthy targets if pods NotReady or wrong port — **Design guidance** aligns with overlay manifests.

## Safe Remediation

1. Fix **backend Ready** first (Git rollback if bad release) — [`git-rollback.md`](./git-rollback.md).
2. Restore controller pods — reschedule via Deployment (**READ-ONLY** watch; delete pod **WARNING — SAFE MUTATION** lab only).
3. Git fix Ingress rules or controller Helm values → Argo sync — preferred over live edit.

## Verification

- VMware: `/health` 200 via VIP; controller **2/2** Ready **Observed** target state.
- AWS: ALB target group **healthy**; `/health` 200 via ALB DNS.

## Rollback

- Git revert ingress/controller overlay → Argo sync.

## Escalation

- MetalLB speaker/L2 issues — platform networking.
- AWS ELB API errors — [`aws-api-failure.md`](./aws-api-failure.md).

## Do Not Do

- Change VIP pool without updating docs/workstation hosts.
- Point Ingress to wrong Service port (8000 lab app).

## Expected Recovery

| Case | RTO |
|------|-----|
| Single controller pod restart | seconds–minutes |
| Surviving replica HA path | **Observed** seconds–minutes with 2 replicas |
| Full VIP loss | until MetalLB + controller restored |

## Observed Project 1 Result

| Item | Status |
|------|--------|
| Pre-HA ingress endpoints 0 on worker loss | **Observed** |
| 2-replica ingress + PDB | **Observed** design |
| Bad app rollout still 200 at ingress (old pods) | **Observed** VMware rollout lab |

## Postmortem Notes

- Separate **edge down** vs **backend down** using curl to VIP and in-cluster Service.
