# NetworkPolicy Troubleshooting Runbook (Project 1 — Section 26)

**Scope:** Pod-to-pod or ingress-to-app connectivity blocked or unexpectedly allowed.  
**Lab namespaces:** `platform-lab` (ingress → app :8000), `security-lab` (default-deny demo).  
**Critical split:** VMware **Calico enforces**; AWS **objects only** in current EKS setup — [`security-rbac.md`](../security-rbac.md).

---

## Symptoms

- VMware: `security-net-client-denied` → server **timeout**; allowed client **OK**.
- AWS: **both** allowed and denied clients **OK** — policies present but not enforced **Observed**.
- `platform-lab`: external HTTP fails while pods Ready — check ingress controller labels vs policy.

## Impact

- False sense of security on AWS if teams assume NP isolation.
- VMware mis-labeling breaks legitimate ingress path.

## Severity

| Env | Misconfigured deny on prod app | Severity |
|-----|------------------------------|----------|
| VMware | Yes | **SEV-2** |
| AWS | NP-only issue | **SEV-3** — verify SGs/CNI |

## First 60 Seconds

1. **READ-ONLY:** `kubectl get networkpolicy -n <ns>`
2. **READ-ONLY:** `kubectl get pods -n <ns> --show-labels`
3. Identify CNI: VMware Calico vs AWS VPC CNI — context from `kubectl config current-context`.

## Preconditions

- Do not install alternate CNI on AWS in this milestone without change record — **Design guidance**.

## Evidence

```powershell
kubectl describe networkpolicy -n platform-lab
kubectl describe networkpolicy -n security-lab
```

Capture client/server pod labels and test command outcomes (no Secret data).

## Triage

| Observation | Meaning |
|-------------|---------|
| VMware deny works | Calico dataplane OK |
| AWS deny fails | **Expected in lab** — not a Calico bug |
| platform-lab broken | ingress-nginx namespaceSelector/podSelector mismatch |

## Diagnosis

### platform-lab (VMware)

Policy allows TCP **8000** from **ingress-nginx** controller pods. If controller labels change in chart upgrade, policy may block — compare Git overlay.

### security-lab matrix **Observed**

| Client | VMware | AWS |
|--------|--------|-----|
| Allowed | OK | OK |
| Denied | timeout | OK |

### NSX / DFW

VMware **NSX automation** is separate from in-cluster NP — [`automation/vmware-nsx-automation-bridge.md`](../automation/vmware-nsx-automation-bridge.md).

## Safe Remediation

1. Fix NetworkPolicy YAML in Git → Argo sync (**WARNING — SAFE MUTATION**).
2. Fix pod labels to match policy selectors in Deployment template (Git).
3. **AWS production isolation:** requires policy-capable CNI (e.g. Calico/Cilium addon) — **Design guidance / Not tested** in Project 1.

## Verification

- Repeat `security-lab` client Job/curl tests from docs.
- VMware: denied client times out; AWS: document if still open path.
- `platform-lab` `/health` via VIP 200.

## Rollback

- Git revert NetworkPolicy commit — [`git-rollback.md`](./git-rollback.md).

## Escalation

- Need AWS enforcement: platform architect for CNI migration plan.
- Corporate firewall/NSX — outside K8s NP scope.

## Do Not Do

- Assume AWS NetworkPolicy YAML protects workloads in this lab.
- `kubectl exec` wget with credentials in command history.

## Expected Recovery

Immediate after sync correct policy/labels (VMware).

## Observed Project 1 Result

| Item | Status |
|------|--------|
| VMware Calico deny | **Observed** |
| AWS no deny observed | **Observed** |
| platform-lab NP unchanged in security milestone | **Observed** doc |

## Postmortem Notes

- State which environment was tested.
- If AWS: note reliance on SG + IAM until CNI upgrade.
