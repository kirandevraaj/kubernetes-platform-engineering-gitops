# Node maintenance: planned vs unplanned

**Scope:** VMware `ckad-lab` and AWS EKS `platform-lab-aws-lab-eks`.  
**Labeling:** Cordon/drain/uncordon semantics are **Design guidance** unless this doc cites a specific Project 1 test.

---

## Concepts

| Action | Purpose | Typical use |
|---|---|---|
| **cordon** | Mark node unschedulable | Planned maintenance start |
| **drain** | Evict workloads (respects PDB) | OS patch, hardware maintenance |
| **uncordon** | Allow scheduling again | Maintenance complete |

| Event | Nature | Project 1 approach |
|---|---|---|
| **Planned maintenance** | Operator-controlled | Cordon/drain → work → uncordon (**Design guidance** — drain not documented as executed in AWS EBS lab) |
| **Unplanned failure** | kubelet stop, EC2 terminate | Wait for control plane + scheduler; replace node capacity |

---

## Observed in Project 1 — unplanned failure

### VMware

- **Method:** kubelet stopped on worker (**Observed** worker failure experiment).
- **Effect:** Node NotReady; NoSchedule/NoExecute taints; reduced capacity.
- **Recovery:** kubelet restarted → node Ready; pods rescheduled (**Observed**).

### AWS

- **Method:** Worker EC2 terminated; **not** `kubectl drain` ([aws-storage-resilience.md](../aws-storage-resilience.md) states drain was not used).
- **Effect:** StatefulSet pod recreated; EBS reattach required same AZ (`ap-south-1b`, vol `vol-05faa26874d720ecd`).
- **Timing:** ~**6.3 minutes** to storage workload healthy (**Observed**).

Temporary extra node group in `ap-south-1b` was used for capacity during experiment — see storage resilience doc.

---

## Planned maintenance (Design guidance)

```text
1. Confirm maintenance window and PDB headroom
2. kubectl cordon <node>          (SAFE MUTATION)
3. kubectl drain <node> --ignore-daemonsets --delete-emptydir-data=...  (SAFE MUTATION — review flags)
4. Perform host/OS/hypervisor work
5. kubectl uncordon <node>        (SAFE MUTATION)
6. Verify pods rescheduled; run post-change checklist
```

**WARNING — DESTRUCTIVE:** Force delete pods or `--force` drain bypasses safety — avoid on stateful workloads without DR plan.

**Not tested in Project 1:** Full cordon/drain cycle on VMware ingress workers with 2-replica ingress HA — validate PDB and second replica before drain.

---

## Cordon/drain vs failure — decision table

| Question | Planned (drain) | Unplanned (failure) |
|---|---|---|
| Node Ready? | Often cordoned but Ready until drain completes | NotReady / gone |
| Pod eviction | Controlled | Sudden termination |
| Stateful + EBS | Ensure second node in **same AZ** before drain | Same-AZ replacement critical (**Observed**) |
| Ingress HA | Need surviving replica on other node (**Observed** 2-replica fix) | Same |

---

## Related

- [runbooks/worker-node-failure.md](../runbooks/worker-node-failure.md)
- [platform-maintenance.md](./platform-maintenance.md)
- [vmware-networking-anatomy.md](../vmware-networking-anatomy.md) (ingress placement)
