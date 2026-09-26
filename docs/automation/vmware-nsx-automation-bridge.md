# VMware / NSX Automation Bridge (Project 1)

**Status:** Section 24 — map prior VMware/NSX operational experience onto modern platform automation concepts.  
**Requirement:** No live NSX fabric required. Mock Manager APIs and inventory JSON are enough to practice the discipline.

This document does **not** authorize changes to the VMware `ckad-lab` cluster networking (Calico, MetalLB, ingress-nginx) or to AWS VPC/EKS. It teaches transferable patterns.

---

## Why this bridge exists

You already know how to think about inventory, topology, transport nodes, edges, managers, segments, firewall rules, and upgrade waves. Platform engineering automation uses the **same cognitive loop** with different APIs:

```text
Discover actual  →  Express desired  →  Diff  →  Apply idempotently
    →  Verify  →  Observe  →  Retry/rollback on failure
```

Python implements the loop; Ansible may push host/OS pieces; Terraform creates cloud infra; Git + Argo CD own Kubernetes workload desired state. NSX Manager REST is “just another API adapter.”

---

## Concept map

| VMware / NSX world | Automation concept | Project 1 analogue |
|--------------------|--------------------|--------------------|
| vCenter / NSX inventory | API discovery / inventory | `platform-automate inventory`, Ansible inventory, boto3 describe, K8s list |
| NSX topology drawings | Desired vs actual model | Dataclasses Desired/Actual/Plan |
| Transport Nodes (TN) | Desired node enrollment state | Ensure object exists + correct profile (idempotent PUT/PATCH) |
| Edge nodes / clusters | Stateful dataplane capacity | Plan capacity changes; serial apply; verify BFD/status |
| NSX Managers | Control-plane endpoints | Client session, auth token, rate limits, leader awareness |
| Segments / Tier-1/0 | Declarative network objects | Kubernetes NetworkPolicy / AWS SG — still GitOps for K8s |
| Distributed firewall rules | Policy-as-desired-state | Idempotent rule sets; never “append forever” |
| Upgrade workflows | Orchestrated rolling change | Waves, health gates, rollback markers — like Argo sync waves + PDB thinking |
| Alarms / Syslog | Observability | Structured logs, reports, Jenkins archives |

---

## 1. API discovery

**NSX habit:** browse Manager UI or `GET /api/v1/...` to learn object IDs and realizations.

**Automation habit:** encode discovery in code:

- Authenticate (token from env — never Git)  
- List managers, transport nodes, edge clusters, segments  
- Normalize into inventory records (id, name, state, revision/etag)  
- Cache briefly; respect rate limits  

**Mock approach:** ship `mocks/nsx/inventory.json` and a tiny REST stub that returns TN/Edge/segment lists. Python doctor checks reachability of the mock base URL.

**Project 1 parallel:** Kubernetes `list_namespace` / `list_namespaced_deployment` and AWS `describe_instances` filtered by tags.

---

## 2. Desired state

**NSX habit:** “This segment should exist on this TZ with this gateway.”

**Automation habit:** declare desired in data (YAML/JSON), not in click-ops memory:

```yaml
# illustrative only — not applied to live NSX
segments:
  - name: lab-seg-a
    transport_zone: overlay-tz
    subnet: 10.10.10.0/24
firewall:
  - name: allow-lab-api
    action: ALLOW
    source: lab-group
    destination: api-group
    ports: ["443"]
```

Diff engine compares desired to discovered actual. Same pattern as Ansible playbooks and Kubernetes manifests.

**Boundary:** Kubernetes app network policy for `platform-lab` remains in Git for Argo CD — do not “fix” it with imperative NSX-style scripts against the live cluster.

---

## 3. Idempotency

**NSX habit:** re-running a rule publish should not duplicate rules.

**Automation habit:**

- GET by name/tag → if missing CREATE → if present PATCH only when fields differ  
- Use natural keys (display_name + policy path) not only opaque UUIDs in desired files  
- Treat `changed=false` as success  

Idempotency is why Ansible modules and Terraform resources beat shell loops — apply the same idea to NSX REST wrappers.

---

## 4. Orchestration

**NSX upgrade habit:** Managers → Controllers → Edges → Hosts, with health checks between waves.

**Automation habit:** Python controller phases:

```text
precheck → drain/disable (if needed) → mutate wave N → verify wave N → next
```

Map to Project 1:

| NSX wave idea | Lab analogue |
|---------------|--------------|
| Precheck cluster health | `platform-automate doctor` / validate |
| Serial edge upgrade | Ansible `serial:` or Python sequential apply |
| Abort on failed realize | verify FAIL → stop → report |
| Maintenance windows | Argo sync windows concept (policy *when*) |

Do not orchestrate live NSX upgrades from this repo without a dedicated change plan — practice on mocks.

---

## 5. Verification

**NSX habit:** realization state `SUCCESS`, datapath status UP, alarm clear.

**Automation habit:** every apply followed by verify returning `PASS|FAIL|UNKNOWN`:

- Object exists with expected fields  
- Status/realization in allowed set  
- Dependent services still healthy  

UNKNOWN is valid when API timeout prevents confirmation — do not claim PASS.

---

## 6. Retry

**NSX habit:** realization lag — wait and re-poll.

**Automation habit:** retry **transient** realize delays and 429s; do not retry auth failures or schema errors. Backoff + timeout budgets mirror boto3/K8s client practice.

---

## 7. Rollback

**NSX habit:** keep prior config revision; outage → restore known-good.

**Automation habit:**

- Save prior desired snapshot before mutate  
- Prefer reverse plan (desired := previous) over uncontrolled delete  
- For GitOps-owned objects: `git revert` + Argo sync  
- For imperative lab objects: compensating API calls documented in the runbook  

Never automate blind rollback of firewall “delete all rules.”

---

## 8. Observability

**NSX habit:** alarms, syslog, traceflow.

**Automation habit:** structured logs (`run_id`, object id, wave, result), archived JSON reports, optional metrics counters. Jenkins stores evidence for interviews and post-mortems.

---

## Workflow templates (mock-friendly)

### A. Inventory / topology report

1. Authenticate to mock Manager  
2. List TN / Edge / Manager / segments  
3. Emit inventory JSON  
4. Exit 0  

### B. Segment ensure (idempotent)

1. Load desired segment list  
2. Discover actual  
3. Plan creates/updates  
4. `--confirm` apply  
5. Verify realization  

### C. Firewall policy converge

1. Desired rule set is **authoritative** (replace semantics within lab policy section)  
2. Diff  
3. Apply minimal changes  
4. Verify hit counters optional / skipped in mock  

### D. Upgrade rehearsal (dry-run)

1. Build wave plan from inventory  
2. Simulate health gates  
3. Write report without calling mutate endpoints  

---

## Mapping prior runbooks to Project 1 runbooks

| Old NSX incident | New doc |
|------------------|---------|
| API timeout / Manager unreachable | [aws-api-failure](../runbooks/aws-api-failure.md) / [automation-failure](../runbooks/automation-failure.md) patterns |
| Realization stuck | [kubernetes-api-failure](../runbooks/kubernetes-api-failure.md) wait/retry thinking |
| Playbook half-applied | [ansible-failure](../runbooks/ansible-failure.md) |
| Script crashed mid-wave | [python-automation](../runbooks/python-automation.md) |

---

## What not to confuse

| Tool | Owns |
|------|------|
| NSX / cloud network fabric APIs | Underlay / overlay network policy engines |
| Kubernetes NetworkPolicy / Calico | In-cluster pod traffic on `ckad-lab` |
| AWS SG / ALB | EKS north-south / instance firewalling (Terraform) |
| Argo CD | Syncing Git NetworkPolicy YAML to clusters |

Python may orchestrate any of these APIs; GitOps still owns Kubernetes objects that Argo manages.

---

## Related

- [Automation architecture](./automation-architecture.md)  
- [Master guide Part XI](./platform-automation-master-guide.md)  
- [Interview notes Q30](../automation-interview-notes.md)  
