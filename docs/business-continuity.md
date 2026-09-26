# Business Continuity for the Platform Lab (Project 1 — Section 25)

**Purpose:** Capture **people, credentials, DNS, certificates, networking, registry, Git, observability, and runbooks** needed to restore platform **capability**—not just Kubernetes pods. This is a **lab BC checklist**, not an enterprise BC/DR certification.

**Targets:**

| Environment | Context | Role |
|-------------|---------|------|
| VMware | `ckad-lab`, nodes `k8s-ctrl-01` / `k8s-worker-01` / `k8s-worker-02`, K8s **1.31.14** | Primary day-to-day platform engineering |
| AWS | `platform-lab-aws`, EKS **`platform-lab-aws-lab-eks`**, K8s **1.36.4**, **`ap-south-1`**, VPC **`vpc-00c54a2d05f84fed6`** | Cloud path, EBS storage lab, ALB ingress |

**Image of record (promotion target):** `kirandevraaj/platform-lab:0.1.4` · digest `sha256:1cca2b5964043fe6c9c09f17d7f86a3572a46699602919d15c45c9a069b872ff`

---

## 1. RTO / RPO at business-capability level

| Capability | Business impact if lost | RPO (intent) | RTO (intent) | OBSERVED |
|------------|-------------------------|--------------|--------------|----------|
| Developers cannot merge to GitHub | Stops all automated delivery | N/A (SaaS) | Hours (org-dependent) | **TBD** |
| Jenkins CI down | No new image builds/promotions | Last promoted tag in Git | Restore Compose controller | **TBD** |
| Docker Hub unavailable | Nodes cannot pull app image | Use digest pin; mirror **TBD** | Cache/mirror **TBD** |
| VMware lab down | Local demos/training halt | Git unchanged | Rebuild VMs **TBD** |
| AWS EKS down | AWS demos halt | Git + Terraform code | Rebuild per runbook **TBD** |
| Stateful demo data (`storage-demo`) | Lab exercise invalid | Snapshot cadence **TBD** | Same-AZ node recovery **≈6.3 min**; full data restore **TBD** |

---

## 2. People and roles (lab)

| Role | Responsibility in recovery | Notes |
|------|----------------------------|-------|
| Platform engineer (you) | Terraform apply, Argo sync, runbooks | Document personal AWS SSO/login path **outside Git** |
| No 24/7 on-call | Lab only | Escalation N/A |
| Future teammate | Clone repo, read Section 25 docs | Onboarding path: README → this file |

**BC gap:** Single-person dependency — acceptable for portfolio lab; note for interviews.

---

## 3. Credentials and secrets (never in Git)

| Secret / credential | Used for | Storage pattern (lab) | Recovery action |
|---------------------|----------|------------------------|-----------------|
| AWS access for Terraform/EKS | `platform-aws-tools` | Host/container credential chain | Restore IAM user/SSO access via AWS account admin |
| `terraform.tfvars` | Public endpoint CIDR allowlist | Local copy only | Recreate from template `terraform.tfvars.example` |
| Jenkins `dockerhub-platform-lab` | Push images | Jenkins credential store | Rotate in Docker Hub + Jenkins UI |
| Jenkins `github-platform-lab` | Promote commits | Jenkins credential store | GitHub PAT/SSH rotate |
| Argo CD admin (if enabled) | Emergency UI | Kubernetes secret in cluster | Reset via Helm/docs **TBD** |
| VMware SSH keys | Node access | Operator workstation | Backup key material securely |

**Rule:** Documentation references **credential names**, not values.

---

## 4. DNS and certificates

| Item | VMware lab | AWS lab |
|------|------------|---------|
| User-facing hostname | `platform-lab.local` (Ingress host) | ALB DNS name from Ingress (no custom Route53 in scope) |
| DNS resolution | Workstation `/etc/hosts` or local DNS → MetalLB VIP | Public ALB hostname (Route53 **out of scope** per Terraform README) |
| TLS | Lab HTTP / optional self-signed **TBD** | ACM on ALB **not configured** in baseline — HTTP path documented |
| BC impact | Wrong hosts file → false “outage” | ALB deleted with cluster → new DNS on rebuild |

**Recovery:** Re-document ALB hostname after rebuild; update bookmarks/runbooks. **OBSERVED rebuild DNS swap: TBD**

---

## 5. Networking continuity

### 5.1 VMware (`192.168.56.0/24`)

| Component | Function | Failure modes |
|-----------|----------|---------------|
| Host-only network | Node connectivity | VMware network reset |
| MetalLB pool `192.168.56.200-210` | Ingress VIP | Pool exhaustion/misconfig |
| Calico | Pod network | CNI outage (see node failure doc) |

**Recovery:** Restore VM networking, verify `kubectl get nodes`, MetalLB speaker, ingress controller.

### 5.2 AWS (`10.50.0.0/16`)

| Component | Function | Failure modes |
|-----------|----------|---------------|
| IGW + NAT | Private node egress | Single NAT AZ failure (`enable_single_nat_gateway=true`) |
| Public subnets | ALB placement | Subnet tag drift |
| Private subnets | Worker nodes | Route table errors |
| Security groups | API + workload | Manual console edits |

**Recovery:** Prefer Terraform forward apply from [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md). **Multi-AZ NAT** is a future cost tradeoff.

---

## 6. Container registry

| Field | Value |
|-------|-------|
| Registry | Docker Hub `kirandevraaj/platform-lab` |
| Immutable reference | Digest `sha256:1cca2b59…872ff` |
| Promotion | Jenkins updates `kubernetes/overlays/local` and `kubernetes/overlays/aws` |

**BC actions if registry unavailable:**

1. Serve from node cache (temporary, unreliable).
2. Mirror to ECR (**not implemented** — listed out of scope in Terraform README).
3. Roll back Git tag to last known pulled digest on nodes (**degrades forward motion**).

**OBSERVED registry failover:** **TBD**

---

## 7. Git and change management

| Item | Location | BC role |
|------|----------|---------|
| Canonical manifests | GitHub repo `kubernetes/` | Restore all desired K8s state |
| GitOps mirrors | `gitops/applications`, `gitops/projects` | Human-readable; bootstrap uses subset |
| Terraform | `terraform/aws` | Restore VPC/EKS |
| Automation | `automation/python`, `automation/ansible` | Operational verification |

**RPO for configuration:** Last commit on tracked branch (typically `main`).  
**Branch protection / signed commits:** **TBD** (personal lab defaults).

---

## 8. Observability during incidents

| Environment | Stack | Use in BC |
|-------------|-------|-----------|
| VMware | kube-prometheus-stack via Argo (`monitoring`) | Confirm app SLO signals, node NotReady |
| AWS | Metrics Server + HPA (Terraform + GitOps); full stack **lighter** | CPU scaling signals; full Grafana on AWS **TBD** |

**BC practice:** During recovery, preserve:

- Argo CD UI / CLI sync status
- `kubectl get events --sort-by=.lastTimestamp`
- ALB target health (AWS console/CLI)

Link: [`kubernetes-platform-observability.md`](./kubernetes-platform-observability.md), [`runbooks/kubernetes-api-failure.md`](./runbooks/kubernetes-api-failure.md).

---

## 9. Runbooks index (Section 25)

| Scenario | Document |
|----------|----------|
| DR vocabulary / ownership | [`disaster-recovery-fundamentals.md`](./disaster-recovery-fundamentals.md) |
| Terraform state loss | [`terraform-dr.md`](./terraform-dr.md) |
| AWS platform rebuild order | [`terraform-recovery-runbook.md`](./terraform-recovery-runbook.md) |
| AWS Backup for EKS | [`aws-backup-eks-dr.md`](./aws-backup-eks-dr.md) |
| AWS API errors | [`runbooks/aws-api-failure.md`](./runbooks/aws-api-failure.md) |
| Kubernetes API errors | [`runbooks/kubernetes-api-failure.md`](./runbooks/kubernetes-api-failure.md) |
| EBS same-AZ node failure | [`aws-storage-resilience.md`](./aws-storage-resilience.md) |
| VMware worker failure | [`vmware-node-failure-resilience.md`](./vmware-node-failure-resilience.md) |
| Automation failures | [`runbooks/automation-failure.md`](./runbooks/automation-failure.md) |

---

## 10. Communication and decision log (template)

Use a private incident note (not Git) during real recovery:

```text
Incident ID:
Start UTC:
Impact (VMware / AWS / CI):
Decision (rebuild vs restore vs wait):
Git SHA:
Terraform state location:
Argo apps affected:
End UTC:
Follow-ups (remote state, snapshots, AWS Backup plan):
```

---

## 11. Gaps to close (honest backlog)

| Gap | Priority for learning |
|-----|------------------------|
| Remote Terraform backend + locking | High |
| EKS enrolled in AWS Backup + test restore | Medium |
| EBS/CSI snapshot schedule for storage lab | Medium |
| Document Argo admin recovery | Medium |
| VMware etcd/control-plane backup | Low (lab scope) |
| ECR mirror for air-gap/registry outage | Low |

---

## 12. Related

- [`toolchain-inventory.md`](./toolchain-inventory.md) — Section 24 pins
- [`design/environment-strategy.md`](./design/environment-strategy.md) — two-target separation
- [`security-rbac.md`](./security-rbac.md) — access patterns
