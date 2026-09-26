# VMware lab cleanup record

**Date:** 2026-09-26  
**Context:** `ckad-lab`  
**Kubernetes:** 1.31.14  
**Action:** Live cluster cleanup only — **Git source preserved**

## Kept (basic reusable lab)

| Component | Notes |
|---|---|
| kubeadm control plane | etcd, apiserver, controller-manager, scheduler |
| Nodes | `k8s-ctrl-01`, `k8s-worker-01`, `k8s-worker-02` — Ready |
| Calico / Tigera | CNI intact |
| CoreDNS | intact |
| kube-proxy | intact |
| Metrics Server | intact (`kubectl top` works) |
| local-path StorageClass | default; provisioner Running |
| Namespaces | `kube-system`, `default`, `kube-public`, `kube-node-lease`, `calico-*`, `tigera-operator`, `local-path-storage` |

## Removed (Project 1 live)

Argo CD (+ Applications/AppProjects/ApplicationSets/CRDs) · kube-prometheus-stack / monitoring · Grafana · KSM · node-exporter · ingress-nginx (Helm) · MetalLB · platform-lab · storage-lab · security-lab · automation-lab · argo-advanced-* / nested / child namespaces · Project ClusterRoles (`security-*`, Argo, MetalLB) · Prometheus Operator / MetalLB / Argo CRDs · leftover `kube-prometheus-stack-kubelet` Service

## Validation performed

| Test | Result |
|---|---|
| 3 nodes Ready | Pass |
| Calico healthy | Pass |
| `kubectl top nodes/pods` | Pass |
| nginx Deployment + Service + DNS | Pass |
| Pod-to-Service HTTP | Pass |
| local-path PVC write → delete Pod → recreate → data persists | Pass |
| Test namespaces deleted after | Pass |

## Not done

- No `kubeadm reset`
- No node/VM destruction
- No Git manifest deletion (`kubernetes/`, `docs/`, etc. intact)
- Portfolio architecture docs unchanged

## Final shape

```text
kubeadm cluster (ckad-lab)
        |
 +------+------+
 |      |      |
ctrl-01 w01   w02
        |
 Kubernetes
 +----+----+----+----+
 |    |    |    |    |
Calico CoreDNS kube-proxy Metrics Server
                        |
                   local-path
```
