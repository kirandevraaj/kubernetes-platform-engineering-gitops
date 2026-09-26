# Ownership boundaries

| Component | Owns | Does not own |
|---|---|---|
| Git | Desired state (manifests, overlays) | Live runtime data, image builds |
| Jenkins | CI: test/build/push/digest/promote | Runtime reconciliation |
| Docker Hub | Artifact storage | Cluster desired state |
| Terraform | AWS infrastructure lifecycle | Application runtime config |
| Argo CD | Continuous reconciliation to Git | Image builds |
| Kubernetes | Runtime scheduling/state | Source code |
| Python | Custom automation logic / CLI | Infra provisioning (TF) / GitOps reconcile |
| Ansible | Config / ops orchestration | CI image publish |
| Prometheus | Metrics scrape/store/query | Dashboards UX (Grafana) |
| Grafana | Visualization | Metric collection |
| AWS | Managed CP, IAM, EC2, EBS APIs | App Git desired state |
| VMware | Lab VMs / underlay | AWS control plane |

See [tool-boundaries.md](./tool-boundaries.md) · ADR 010.
