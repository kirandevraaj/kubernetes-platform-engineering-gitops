# Pod Not Ready Runbook (Project 1 — Section 26)

**Scope:** Pod **Running** but not **Ready** — readiness probe failures, startup probe delays, init containers incomplete.  
**Lab anchor:** VMware `0.1.5` intentional `/health` **503** when `APP_ENVIRONMENT=local-gitops` — [`vmware-rollout-failure-rollback.md`](../vmware-rollout-failure-rollback.md).

---

## Symptoms

- `kubectl get pods`: `0/1 Ready` or `1/2 Ready` while STATUS is Running.
- `kubectl describe pod`: `Readiness probe failed` on `/health`.
- Pod IP **absent** from Service Endpoints.
- RollingUpdate stuck: surge pod NotReady, old pods still Ready.

## Impact

- NotReady pods **do not receive Service traffic** (ClusterIP/Endpoints model).
- With `maxUnavailable: 0`, old replicas continue serving — **Observed** during bad `0.1.5` rollout.
- Argo may report **Degraded** / **Progressing** while external HTTP still 200.

## Severity

| Condition | Severity |
|-----------|----------|
| Surge NotReady, old Ready ≥1 | **SEV-3** — release gate working |
| All pods NotReady | **SEV-2** |
| Readiness flapping under load | **SEV-2** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get pods,endpoints -n platform-lab`
2. **READ-ONLY:** `kubectl describe pod <not-ready-pod> -n platform-lab` — probe section
3. **READ-ONLY:** Exec/curl from pod network if allowed: check `/health` locally
4. Compare `/version` at ingress vs failing pod label

## Preconditions

- Understand probe path (`/health`), period, and failure threshold in Deployment (Git).
- Distinguish VMware overlay ConfigMap (`local-gitops`) vs AWS (`aws-eks-gitops`).

## Evidence

```powershell
kubectl get deploy platform-lab -n platform-lab -o yaml | Select-String -Pattern readinessProbe,image,digest
kubectl logs -n platform-lab <pod> --tail=100
curl.exe -H "Host: platform-lab.local" http://192.168.56.200/health
```

Record probe HTTP status and `APP_ENVIRONMENT` from env (values only, no Secrets).

## Triage

| Pattern | Cause |
|---------|-------|
| 503 on `/health` after promotion | Bad release / env-gated fault |
| Connection refused | App not listening yet — startup probe |
| Timeout | NetworkPolicy (VMware) or dependency down |
| Only new RS | Rollout gate — see [`failed-rollout.md`](./failed-rollout.md) |

## Diagnosis

1. Confirm **Endpoints** only list Ready pod IPs.
2. Check ReplicaSet generation: new template vs old.
3. **NetworkPolicy (VMware):** Calico enforces — wrong ingress may block probes from kubelet? (probe uses pod network; usually local). Client path from ingress-nginx documented in [`networkpolicy-troubleshooting.md`](./networkpolicy-troubleshooting.md).
4. **AWS:** same NetworkPolicy YAML may exist but **not enforce** in lab VPC CNI — **Observed** [`security-rbac.md`](../security-rbac.md).

## Safe Remediation

1. **Bad Git release:** revert digest to `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff` → push → Argo sync (**SAFE MUTATION** on Git).
2. **Probe misconfiguration:** fix in overlay YAML, not live patch (unless break-glass).
3. **WARNING — SAFE MUTATION:** Deleting NotReady surge pod alone does **not** fix bad image — RS recreates same template.

Avoid primary rollback via `kubectl rollout undo`.

## Verification

- All targeted pods Ready; Endpoints count = desired ready replicas.
- `/health` 200 at edge (MetalLB VIP or ALB).
- Argo **Healthy**.

## Rollback

Git revert path — [`git-rollback.md`](./git-rollback.md). **Observed:** ~6s to healthy after `0.1.4` restore.

## Escalation

- CI/promotion pipeline if digest wrong on `main`.
- Ingress/backend mismatch — [`service-endpoint-troubleshooting.md`](./service-endpoint-troubleshooting.md).

## Do Not Do

- Lower readiness thresholds in cluster only to “go green”.
- Remove readiness probe as hotfix on production-like apps.
- Assume AWS and VMware behave identically for env-gated config.

## Expected Recovery

| Fix | Time |
|-----|------|
| Git digest rollback | seconds–minutes |
| Pod recreate after fix | **~10s** VMware **Observed** |

## Observed Project 1 Result

| Item | Status |
|------|--------|
| `0.1.5` NotReady surge, `0.1.4` serves traffic | **Observed** |
| AWS same digest stays Ready (env gate) | **Observed** |
| Ingress `/health` 200 while new pod 503 | **Observed** |

## Postmortem Notes

- Document whether incident was **release** vs **infra** vs **probe tuning**.
- Add CI smoke against `/health` per overlay before merge to `main`.
