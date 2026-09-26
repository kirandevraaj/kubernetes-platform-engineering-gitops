# VMware Kubernetes Networking Anatomy

**Date:** 2026-09-26  
**Environment:** VMware / on-prem kubeadm (`ckad-lab`)  
**Scope:** Read-only investigation (no network mutation)  
**Motivation:** During worker-02 kubelet outage (commit `84c3478`), survivor Pod stayed Ready and Service endpoints went 2→1, yet external `/health` often returned connection failure (`000`).  

---

## 1. Cluster Network Topology

| Node | Role | Lab IP (`lab0`) | Pod CIDR (Calico) |
|---|---|---|---|
| `k8s-ctrl-01` | control-plane | `192.168.56.10` | `10.244.218.0/26` |
| `k8s-worker-01` | worker | `192.168.56.11` | `10.244.36.192/26` |
| `k8s-worker-02` | worker | `192.168.56.12` | `10.244.118.64/26` |

Primary L2 lab NIC: **`lab0`** (`192.168.56.0/24`).  
Secondary: `nat0` (`192.168.50.0/24`) for host NAT / Calico cross-subnet VXLAN underlay.

---

## 2. Physical / VM Network

```text
Windows host (192.168.56.1)
        │
        │ VMware host-only / lab segment
        ▼
┌─────────────────────────────────────────────┐
│  192.168.56.0/24  (lab0 on each VM)         │
│  .10 ctrl · .11 worker-01 · .12 worker-02   │
│  .200 MetalLB VIP (ingress-nginx)           │
│  .201 MetalLB VIP (Grafana)                 │
└─────────────────────────────────────────────┘
```

Windows ARP (live): `192.168.56.200 → 00-50-56-a1-11-01` = **`k8s-worker-01`** MAC (matches `ip neigh` for `.11`).

---

## 3. Calico Pod Networking

| Component | Namespace | Type | Placement |
|---|---|---|---|
| `calico-node` | `calico-system` | DaemonSet ×3 | all nodes · image `quay.io/calico/node:v3.30.7` |
| `csi-node-driver` | `calico-system` | DaemonSet ×3 | all nodes |
| `calico-typha` | `calico-system` | Deployment ×2 | ctrl + worker-01 |
| `calico-kube-controllers` | `calico-system` | Deployment ×1 | ctrl |
| `calico-apiserver` | `calico-apiserver` | Deployment ×2 | ctrl + worker-01 |

**IP pool** `default-ipv4-ippool`: `10.244.0.0/16` · `vxlanMode: CrossSubnet` · `ipipMode: Never` · `natOutgoing: true`.

Pod interfaces appear as `cali*` / `vxlan.calico` on nodes.

---

## 4. Kubernetes Services

| Service | NS | Type | ClusterIP | EXTERNAL-IP | Ports |
|---|---|---|---|---|---|
| `ingress-nginx-controller` | `ingress-nginx` | **LoadBalancer** | `10.98.173.180` | **`192.168.56.200`** | 80→NodePort **30080**, 443→**30443** |
| `platform-lab` | `platform-lab` | **ClusterIP** | `10.107.132.189` | — | **8000→8000** |
| Grafana LB | `monitoring` | LoadBalancer | … | **`192.168.56.201`** | 80 |

MetalLB annotation on ingress Service: `metallb.io/ip-allocated-from-pool: lab-pool`.

---

## 5. EndpointSlices

**platform-lab** (`platform-lab-s97kd`):

| Pod IP | Node | Ready |
|---|---|---|
| `10.244.36.194` (`…-65xpb`) | worker-01 | true |
| `10.244.118.97` (`…-rhnrf`) | worker-02 | true |

**ingress-nginx-controller** (historical finding from this investigation — **resolved**; see §8 and [vmware-ingress-ha.md](./vmware-ingress-ha.md)):

| Pod IP | Node | Ready |
|---|---|---|
| `10.244.118.86` (`ingress-nginx-controller-bd6958564-m2pvm`) | **worker-02 only** | true |

At investigation time there was **exactly one** ingress controller endpoint. Losing worker-02 removed **all** ingress Service backends. That SPOF was fixed by raising ingress to **2 replicas** with soft topology spread across worker-01 / worker-02.

---

## 6. kube-proxy

- DaemonSet `kube-proxy` ×3 (`registry.k8s.io/kube-proxy:v1.31.14`) on all nodes.
- ConfigMap `kube-system/kube-proxy`: `mode: ""` (default).
- Live evidence: `iptables -t nat -L KUBE-SERVICES` present on control-plane → **iptables mode** (default), not IPVS.

---

## 7. MetalLB

| Item | Value |
|---|---|
| Version | **v0.16.1** (`quay.io/metallb/controller|speaker:v0.16.1`) |
| Controller | Deployment ×1 · currently on **worker-02** |
| Speakers | DaemonSet ×3 · ctrl + both workers · `kubernetes.io/os=linux` only |
| IPAddressPool | `lab-pool` · **`192.168.56.200–192.168.56.210`** · autoAssign |
| L2Advertisement | `lab-l2` · pools: `[lab-pool]` · **no** nodeSelectors / interface filters |

**VIP ownership (live):** `ServiceL2Status` for `ingress-nginx/ingress-nginx-controller` → **`node: k8s-worker-01`**.  
Event after prior outage: `announcing from node "k8s-worker-01" with protocol "layer2"`.

All three speakers are eligible; one speaker wins L2 leadership per Service.

---

## 8. ingress-nginx

| Item | Value |
|---|---|
| Chart / image | ingress-nginx **4.15.1** / controller **v1.15.1** |
| Workload type | **Deployment** (not DaemonSet) |
| Replicas | **2** (was **1** at investigation — SPOF fixed; see [vmware-ingress-ha.md](./vmware-ingress-ha.md)) |
| Node placement | **worker-01 + worker-02** (was worker-02 only) |
| Affinity / topology spread | soft `topologySpreadConstraints` on `kubernetes.io/hostname` (`ScheduleAnyway`) |
| PDB | `ingress-nginx-controller` · `minAvailable: 1` |
| Service `externalTrafficPolicy` | **`Cluster`** |
| Service `internalTrafficPolicy` | Cluster |
| sessionAffinity | None |
| GitOps | Argo `platform-lab-local` owns HA Deployment fields + PDB + MetalLB Service patch; Helm release retained |

---

## 9. platform-lab Ingress

| Field | Value |
|---|---|
| Name | `platform-lab` |
| Class | `nginx` |
| Host | `platform-lab.local` |
| Path | `/` Prefix → Service `platform-lab:8000` |
| ADDRESS | `192.168.56.200` |

**NetworkPolicy** `platform-lab` (Ingress): allows TCP/8000 only from:

1. pods in `ingress-nginx` with ingress-controller labels  
2. namespace `monitoring`

Direct curls from control-plane to Pod IP / app ClusterIP fail (**expected** under this policy). Ingress and monitoring paths are allowed.

---

## 10. End-to-End Traffic Path

Verified live path:

```text
Windows client
   │  HTTP Host: platform-lab.local
   ▼
192.168.56.200:80          ← MetalLB VIP (L2 ARP → worker-01 MAC today)
   │
   ▼
Service/ingress-nginx-controller (LoadBalancer)
  ClusterIP 10.98.173.180 · NodePorts 30080/30443
  externalTrafficPolicy=Cluster
   │  kube-proxy iptables
   ▼
Pod ingress-nginx-controller (replicas=2 after HA fix)
  worker-01 + worker-02
   │  Ingress rule host/path
   ▼
Service/platform-lab (ClusterIP 10.107.132.189:8000)
   │  EndpointSlice
   ├──────────────────────┐
   ▼                      ▼
Pod …-65xpb            Pod …-rhnrf
10.244.36.194          10.244.118.97
k8s-worker-01          k8s-worker-02
```

> Historical note: at first investigation the path terminated at a **single** ingress Pod on worker-02 (`…-m2pvm` / `10.244.118.86`). That SPOF is documented above and fixed in [vmware-ingress-ha.md](./vmware-ingress-ha.md).
---

## 11. Internal Service Path

```text
ingress-nginx Pod
  → platform-lab ClusterIP:8000
  → kube-proxy
  → Ready EndpointSlice backends (app pods)
```

App Pods are not meant to be reached directly from arbitrary namespaces (NetworkPolicy).

---

## 12. External VIP Path

```text
Client → VIP:80 → (any node via Cluster policy / L2 destination)
  → kube-proxy DNAT to Ready ingress-nginx endpoints
  → single ingress Pod on worker-02
  → platform-lab Service → app Pod
```

Connectivity tests (control-plane / Windows), healthy cluster:

| Source | Destination | Result |
|---|---|---|
| ctrl | VIP `192.168.56.200` + Host header | **200** |
| ctrl | ingress ClusterIP `10.98.173.180` | **200** |
| ctrl | NodePort `.11:30080` / `.12:30080` | **200** |
| Windows | VIP + Host header | **200** |
| ctrl | app ClusterIP / Pod IPs | **fail** (NetworkPolicy) |

---

## 13. Node Failure Traffic Impact

Prior experiment failed **`k8s-worker-02`** (kubelet stop).

| Layer | Effect when worker-02 NotReady |
|---|---|
| App survivor on worker-01 | Stays Ready |
| App Service endpoints | 2 → **1** (survivor) |
| **ingress-nginx endpoints** | 1 → **0** (only replica was on worker-02) |
| External VIP `/health` | Often **`000`** — nothing healthy behind LB VIP |
| MetalLB speakers | worker-02 speaker unhealthy; VIP re-announced from **worker-01** (event + ServiceL2Status) |
| HPA / Argo | No scale / Synced |

**Conclusion:** External failure was **not** “Service lost the last app pod.” It was **“ingress data plane lived only on the failed node.”**

---

## 14. externalTrafficPolicy

| Setting | Behavior |
|---|---|
| **Cluster** (actual) | Packets to VIP/NodePort may land on any node; kube-proxy **forwards** to Ready backends cluster-wide. Source NAT; client IP not preserved. |
| **Local** | Node only forwards to **local** Ready endpoints; otherwise drops. Needs backends on the announcing/receiving node. |

This cluster uses **`Cluster`**. That setting did **not** cause the outage by itself: with **zero** Ready ingress endpoints, both Cluster and Local fail for VIP→ingress traffic.

---

## 15. MetalLB L2 Failover

- Speakers on all nodes; L2Advertisement unrestricted → any Ready node with a speaker can announce.
- On speaker/node loss, another speaker takes VIP and gratuitous ARP updates clients’ neighbor cache (clients may briefly use stale MAC).
- Failover is typically seconds, not minutes — **but** VIP ownership alone cannot serve HTTP if ingress-nginx has no Ready Pods.

---

## 16. Evidence From Previous Node Failure

| Observation | Evidence |
|---|---|
| Failed node = worker-02 | Experiment `84c3478` |
| Sole ingress Pod on worker-02 | Live placement + EndpointSlice |
| ingress Event `NodeNotReady` on that Pod | `kubectl get events -n ingress-nginx` |
| VIP later announced from worker-01 | Event `nodeAssigned` + `ServiceL2Status` |
| App survivor Ready + 1 endpoint | Prior node-failure doc |
| External `/health` → 000 | Prior node-failure measurements |

---

## 17. Confirmed / Likely / Possible Causes

### CONFIRMED

1. **Single-replica ingress-nginx scheduled only on the failed worker** → ingress Service lost all endpoints when worker-02 failed → external VIP path broken while app survivor remained Ready.

### LIKELY

2. **Transient MetalLB L2 re-election / ARP cache lag** while VIP moved off worker-02 — may add brief packet loss; does not explain sustained failure once VIP is elsewhere **without** an ingress Pod.
3. During outage, kube-proxy still had **no Ready ingress backends**, so NodePort/VIP→ingress DNAT had nowhere healthy to send traffic.

### POSSIBLE

4. Clients holding stale ARP for a MAC on the failed node until neighbor timeout / GARP from new speaker.
5. Brief disruption of Calico VXLAN paths for pods on the failed node (app + ingress on that node).

### NOT SUPPORTED (by current evidence)

- **`externalTrafficPolicy=Local`** — live value is **`Cluster`**.
- “App Service had zero endpoints” — survivor kept one endpoint.
- “HPA / Argo caused external outage” — they did not.
- “NetworkPolicy blocked ingress” — policy explicitly allows ingress-nginx; healthy-path tests succeed through ingress.

---

## 18. Troubleshooting Flow

```text
External /health fails
        │
        ▼
Client → VIP:80 ?  (curl -H Host … http://192.168.56.200/health)
        │ fail
        ▼
ARP/MAC for VIP?  (arp -a / ip neigh)  ← L2 / MetalLB announce
        │
        ▼
ServiceL2Status / speaker events  ← which node announces?
        │
        ▼
ingress-nginx Pods Ready?  (kubectl get pods -n ingress-nginx -o wide)
        │ none Ready
        ▼
INGRESS DATA PLANE DOWN  ← (this lab’s case)
        │
        ▼
ingress Endpoints/EndpointSlice empty?
        │
        ▼
Ingress object → correct Service/port?
        │
        ▼
platform-lab EndpointSlice Ready?
        │
        ▼
From ingress Pod: curl app Pod:8000/health
        │
        ▼
App /health / NetworkPolicy / Calico
```

Separate concerns:

| Class | Checks |
|---|---|
| L2 | VIP ARP, ServiceL2Status, speaker Ready |
| Service/LB | ingress Service endpoints, externalTrafficPolicy |
| Ingress | controller replicas/placement, Ingress rules |
| App | EndpointSlice, NetworkPolicy, Pod Ready |

---

## 19. Candidate Future Failure Experiments

Completed after this anatomy doc:

1. ~~Fail the node hosting the sole ingress controller~~ — validated; then fixed via HA.  
2. ~~Raise ingress-nginx to ≥2 replicas with topology spread; re-test single-worker loss~~ — done in [vmware-ingress-ha.md](./vmware-ingress-ha.md) (worker-01 and worker-02 kubelet-stop tests both kept external `/health` available).

Still open:

3. Compare MetalLB announce node vs ingress endpoint node under `externalTrafficPolicy=Local` (would be a config change — future decision).  
4. Grafana VIP (`192.168.56.201`) resilience (also LB via MetalLB).  
5. Full VM power-off vs kubelet stop for measured ARP/MetalLB interrupt.

---

## Appendix A — ASCII architecture (verified)

```text
                 Windows (192.168.56.1)
                          |
                          | HTTP + Host: platform-lab.local
                          v
                 192.168.56.200 (MetalLB VIP)
                    announced L2 by speaker
                    (today: k8s-worker-01)
                          |
          +---------------+---------------+
          | kube-proxy (iptables) on nodes|
          +---------------+---------------+
                          |
                          v
         Service/ingress-nginx-controller
         LB / ClusterIP / NodePort 30080
         externalTrafficPolicy=Cluster
                          |
                          v
         ingress-nginx Pods (replicas=2; was 1 at first investigation)
         worker-01 + worker-02 (topology spread)
                          |
                          v
         Ingress/platform-lab (class nginx)
                          |
                          v
         Service/platform-lab :8000
         ClusterIP 10.107.132.189
                          |
              +-----------+-----------+
              v                       v
     Pod 10.244.36.194         Pod 10.244.118.97
     worker-01                 worker-02

Speakers: ctrl + w01 + w02 (DaemonSet)
Calico node: ctrl + w01 + w02 (DaemonSet)
```

---

## Appendix B — AWS conceptual contrast (read-only)

| VMware | AWS (platform-lab ALB path) |
|---|---|
| Client → **MetalLB** → **ingress-nginx** → Service → Pod | Client → **AWS ALB** → **AWS LB Controller** → Pod IP |
| L2 VIP + NodePort | Cloud NLB/ALB; no MetalLB |
| Single ingress Deployment is a SPOF on one worker | ALB targets registered across nodes/AZs by controller |

Do not modify AWS for this milestone.
