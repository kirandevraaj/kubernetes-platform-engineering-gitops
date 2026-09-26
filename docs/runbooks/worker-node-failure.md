# Worker Node Failure Runbook (Project 1 — Section 26)

**Scope:** Worker node **NotReady**, unreachable, or lost — VMware kubeadm vs AWS EKS managed node group.  
**Related:** [`pod-failure.md`](./pod-failure.md), [`ebs-attach-troubleshooting.md`](./ebs-attach-troubleshooting.md), [`ingress-unavailable.md`](./ingress-unavailable.md).

---

## Symptoms

- `kubectl get nodes`: worker **NotReady** / **Unknown**.
- Pods **Pending** or **Terminating** stuck on lost node.
- VMware: VM powered off; AWS: EC2 instance terminated or unhealthy.

## Impact

- Workloads reschedule to surviving nodes if capacity exists.
- **Observed AWS:** EBS volume reattach to new node **~6.3 min** for `storage-demo-0` in `ap-south-1b`.
- **Observed VMware (historical):** Single ingress on **worker-02** caused **ingress SPOF** until 2-replica HA — [`vmware-ingress-ha.md`](../vmware-ingress-ha.md).

## Severity

| Condition | Severity |
|-----------|----------|
| Surviving workers Ready, apps reschedule | **SEV-3** |
| All workers down | **SEV-1** |
| Stateful pod + AZ-bound volume pending | **SEV-2** |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get nodes -o wide`
2. **READ-ONLY:** `kubectl get pods -A -o wide | Select-String -Pattern NotReady,Pending,NodeLost`
3. Identify **platform** vs **storage** vs **ingress** pods on failed node.

---

## VMware (`ckad-lab`)

### Evidence (READ-ONLY)

```powershell
kubectl config use-context ckad-lab
kubectl describe node <worker>
kubectl get pods -n ingress-nginx -o wide
kubectl get pods -n platform-lab -o wide
```

Hypervisor: verify VM power state (out-of-band — **Design guidance**, not automated in repo).

### Diagnosis

- Control plane on `k8s-ctrl-01` — single CP **Design guidance** risk; workers carry workload.
- MetalLB L2 speaker must run on nodes with reachable LAN — see [`metallb-vip-failure.md`](./metallb-vip-failure.md).
- Pod reschedule **Observed ~10s** for simple Deployment pods when capacity exists.

### Safe Remediation

1. Restore VM / kubelet (**WARNING — SAFE MUTATION** — infrastructure action).
2. If node permanently lost: drain/cordon when API still talks to node — **WARNING — SAFE MUTATION:** `kubectl drain <node> --ignore-daemonsets --delete-emptydir-data` (use only when node recoverable or confirmed dead per ops policy).
3. Do **not** delete PVCs on platform-lab due to node loss alone.

### Observed Project 1 Result (VMware)

| Item | Status |
|------|--------|
| Ingress SPOF when only controller on lost worker | **Observed** pre-HA |
| 2 ingress replicas + spread | **Observed** post-HA design |
| Pod replace timing | **Observed** ~10s |

---

## AWS (EKS `platform-lab-aws`)

### Evidence (READ-ONLY)

```powershell
kubectl config use-context <aws-context>
kubectl get nodes -L topology.kubernetes.io/zone
kubectl describe pod storage-demo-0 -n storage-lab
kubectl get events -n storage-lab --sort-by='.lastTimestamp'
```

Note instance ID, AZ (`ap-south-1b` for lab volume `vol-05faa26874d720ecd`).

### Diagnosis

- Managed node group replaces failed instance — **Design guidance** for AWS automation.
- EBS **same AZ** required — cross-AZ Pending is expected block — [`ebs-storage-recovery.md`](./ebs-storage-recovery.md).
- Lab hit **17 pods/node** — may block reschedule until scale-out — [`dr-lab-evidence.md`](../dr-lab-evidence.md).

### Safe Remediation

1. Wait for MNG replacement and CSI **AttachVolume** (**READ-ONLY** watch).
2. **WARNING — SAFE MUTATION:** Temporary `desiredSize` increase for capacity in same AZ — **Observed** during DR drill.
3. Avoid manual `aws ec2 attach-volume` — EBS CSI owns attach.

### Observed Project 1 Result (AWS)

| Item | Status |
|------|--------|
| Node terminate → pod Ready with same volume | **Observed ~6.3 min** |
| Volume ID unchanged after recovery | **Observed** |

---

## Verification (both)

- All nodes needed for capacity **Ready**.
- Critical apps: Deployment Ready counts; StatefulSet ordinal Running.
- Ingress/ALB targets healthy — [`ingress-unavailable.md`](./ingress-unavailable.md), [`aws-alb-unhealthy.md`](./aws-alb-unhealthy.md).

## Rollback

- Infrastructure: Terraform/VM restore — [`terraform-infrastructure-recovery.md`](./terraform-infrastructure-recovery.md).
- App config unchanged — GitOps unchanged unless node labels affected scheduling.

## Escalation

- Control plane failure VMware — **Design guidance** — rebuild kubeadm cluster; restore from Git/Argo.
- EKS API failure — [`kubernetes-api-failure.md`](./kubernetes-api-failure.md), [`aws-api-failure.md`](./aws-api-failure.md).

## Do Not Do

- Terminate nodes with sole copy of non-replicated data without DR plan.
- Force-delete StatefulSet pods without checking PVC retention.
- Assume AWS and VMware recovery times match.

## Expected Recovery

| Env | Order of magnitude |
|-----|---------------------|
| VMware Deployment pod | ~10s |
| AWS EBS StatefulSet same volume | ~6.3 min **Observed** |
| EKS new worker join | minutes **Design guidance** |

## Postmortem Notes

- Node name, AZ, workloads affected, attach duration.
- Capacity headroom / pod density limits.
