# Operations command reference (safe-first)

Grouped **READ-ONLY** commands for triage. See [runbook-template.md](../runbooks/runbook-template.md) for classification rules.  
**Never:** `kubectl get secrets -o yaml`, print kubeconfig, or `aws` calls that dump credentials.

Automation alternative: `platform-automate doctor` — [automation/automation-command-reference.md](../automation/automation-command-reference.md).

---

## Kubernetes

| Command | Purpose | Class | Context |
|---|---|---|---|
| `kubectl config current-context` | Avoid wrong cluster | READ-ONLY | Both |
| `kubectl get nodes -o wide` | Node health | READ-ONLY | Both |
| `kubectl get pods -A -o wide` | Workload placement | READ-ONLY | Both |
| `kubectl get deploy,rs,hpa -n platform-lab` | Rollout/HPA | READ-ONLY | Both |
| `kubectl describe pod <p> -n <ns>` | Events, probes | READ-ONLY | Both |
| `kubectl logs deploy/platform-lab -n platform-lab --tail=200` | App logs | READ-ONLY | Both |
| `kubectl get endpointslices -n platform-lab` | Endpoint count | READ-ONLY | Both |
| `kubectl get pvc,pv -A` | Storage | READ-ONLY | Both |
| `kubectl get volumeattachment` | EBS attach path | READ-ONLY | AWS |
| `kubectl get events -A --sort-by='.lastTimestamp'` | Recent warnings | READ-ONLY | Both |
| `kubectl auth can-i --list --as=system:serviceaccount:ns:sa` | RBAC debug | READ-ONLY | Both |
| `kubectl top nodes` / `kubectl top pods` | Saturation | READ-ONLY | If metrics-server up |

| Command | Purpose | Class |
|---|---|---|
| `kubectl cordon <node>` | Planned maintenance | SAFE MUTATION |
| `kubectl uncordon <node>` | End maintenance | SAFE MUTATION |
| `kubectl delete pod <name> -n <ns>` | Force reschedule | DESTRUCTIVE — lab only |

---

## Argo CD

| Command | Purpose | Class |
|---|---|---|
| `kubectl get applications -n argocd` | Sync/health | READ-ONLY |
| `kubectl describe application <name> -n argocd` | Conditions, errors | READ-ONLY |
| `argocd app diff <name>` | Drift detail | READ-ONLY | If CLI configured |

**GitOps rollback:** Git revert + push — SAFE MUTATION in Git; not `kubectl rollout undo`.

---

## AWS (read-mostly)

| Command | Purpose | Class |
|---|---|---|
| `aws eks describe-cluster --name platform-lab-aws-lab-eks --region ap-south-1` | Control plane | READ-ONLY |
| `aws ec2 describe-volumes --volume-ids vol-05faa26874d720ecd --region ap-south-1` | EBS state | READ-ONLY |
| `aws elbv2 describe-target-health ...` | ALB targets | READ-ONLY |

**Do not:** manual `attach-volume` / `detach-volume` during triage.

---

## Terraform

| Command | Purpose | Class |
|---|---|---|
| `terraform fmt -check` | Format | READ-ONLY |
| `terraform validate` | Syntax | READ-ONLY |
| `terraform plan` | Intent diff | READ-ONLY |
| `terraform apply` | Infra change | SAFE MUTATION — review required |
| `terraform destroy` | Tear down | DESTRUCTIVE |

Path: `terraform/aws`. State risks: [terraform-dr.md](../terraform-dr.md).

---

## Git

| Command | Purpose | Class |
|---|---|---|
| `git log -10 --oneline` | Recent changes | READ-ONLY |
| `git show <sha>` | Change detail | READ-ONLY |
| `git revert <sha>` | Rollback commit | SAFE MUTATION |

---

## Jenkins / Python / Ansible

| Command | Purpose | Class |
|---|---|---|
| Jenkins UI build log | CI failure stage | READ-ONLY |
| `platform-automate doctor` | Workstation/cluster connectivity | READ-ONLY |
| `ansible-playbook ... --check` | Dry run | READ-ONLY |

Windows Ansible CLI: **not reliably on PATH** — [toolchain-inventory.md](../toolchain-inventory.md).

---

## Application health (VMware)

```text
curl.exe -sS -o NUL -w "%{http_code}" -H "Host: platform-lab.local" http://192.168.56.200/health
```

Class: **READ-ONLY**

---

## Related

- [triage-framework.md](../troubleshooting/triage-framework.md)
- [operational-antipatterns.md](./operational-antipatterns.md)
