# Change ownership boundaries (Project 1)

Clear ownership prevents `kubectl edit` wars and orphan infrastructure.

| Owner | Owns | Does not own |
|---|---|---|
| **Developer** | Application code, unit tests, container behavior | Live cluster desired state directly |
| **Git repository** | Declarative desired state (manifests, overlays, pins) | Running process memory |
| **Jenkins** | CI: build, test, push image, digest capture, promotion triggers | `kubectl apply` production app (**Observed policy**) |
| **Argo CD** | Reconcile Git → cluster; selfHeal where enabled | Application business logic |
| **Terraform** | AWS VPC, EKS, node groups, add-ons (when applied) | In-cluster Deployment edits |
| **Python / Ansible automation** | Doctor, read-mostly ops, approved mutations in allow-listed NS | Ad-hoc cluster-admin changes |
| **Operator** | Incident response, evidence, controlled changes via Git/IaC | Bypassing review for durable changes |
| **AWS** | EKS control plane, EC2, EBS, ALB data plane | Pod manifest source of truth |

---

## GitOps change flow (Observed model)

```text
Branch → PR → merge → Jenkins (if app) → digest in Git → Argo sync → verify
```

See [architecture/gitops-flow.md](../architecture/gitops-flow.md), [runbooks/gitops-change.md](../runbooks/gitops-change.md) when present.

---

## Environment split

| Component | VMware | AWS |
|---|---|---|
| Argo CD version | v3.5.3 | v3.1.0 |
| Context | `ckad-lab` | `platform-lab-aws` |
| Ingress | MetalLB + ingress-nginx | ALB |

Treat as **two control planes** — do not assume one Argo change applies to both.

---

## Related

- [pre-change-checklist.md](../checklists/pre-change-checklist.md)
- [security-rbac.md](../security-rbac.md)
- [toolchain-inventory.md](../toolchain-inventory.md)
