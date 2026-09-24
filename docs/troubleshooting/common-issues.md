# Common issues

Add an entry when a problem recurs. Include the symptom, the cause, and the fix that was actually used.

## Host cannot ping or SSH to 192.168.56.10–.12

**Symptom.** `ssh k8s-ctrl-01` hangs. `ping 192.168.56.10` gets no reply. `vmrun` still shows the VMs running, and VMware Tools reports guest addresses `192.168.56.10`, `.11`, and `.12`.

**Cause.** The nodes use host-only `VMnet1` (`192.168.56.0/24`). On 24 September 2026 the host adapter `VMware Network Adapter VMnet1` had fallen back to a `169.254.x.x` address, so Windows had no route to `192.168.56.0/24`. The guests themselves were up; their NAT interfaces on `192.168.50.0/24` still answered.

**Fix used.** Set a static address on the host adapter:

```text
netsh interface ipv4 set address name="VMware Network Adapter VMnet1" static 192.168.56.1 255.255.255.0
```

That command needs an elevated shell. After it, ping and SSH to `.10`, `.11`, and `.12` succeeded. The guest `lab0` addresses were already correct and were left unchanged.

## kubectl on the workstation talks to an unexpected cluster

**Symptom.** Commands succeed, but nodes or namespaces do not match the lab.

**Check.** `kubectl config current-context`. The lab context observed during bootstrap was `ckad-lab`. `docker-desktop` is also configured and points somewhere else. Confirm the context before any future write.

## Prometheus cannot scrape platform-lab /metrics

**Symptom.** ServiceMonitor exists but the Prometheus target is down, or Grafana request panels stay empty.

**Checks.**

1. Image tag is `0.1.3` or newer (exposes `/metrics`).
2. Local NetworkPolicy allows namespace `monitoring` to TCP/8000 (local overlay patch).
3. CRD `servicemonitors.monitoring.coreos.com` exists (Application `platform-lab-observability` Healthy).
4. Generate traffic: `curl.exe -sS -H "Host: platform-lab.local" http://192.168.56.200/health`.

## Grafana has no browser-reachable address

**Symptom.** Grafana pods are Ready but there is no EXTERNAL-IP, or the browser cannot open Grafana.

**Checks.** Service type must be LoadBalancer (not ClusterIP). MetalLB pool `lab-pool` still has free addresses. Do not point Grafana at VIP `192.168.56.200` (that VIP is ingress-nginx). Discover the assigned address with `kubectl get svc -n monitoring -l app.kubernetes.io/name=grafana -o wide`.
