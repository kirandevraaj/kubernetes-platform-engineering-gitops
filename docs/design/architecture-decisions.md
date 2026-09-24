# Architecture decisions

Record a decision here when it is accepted. Until then, items below are open.

## ADR-000: Repository starts as documentation and layout

- **Status:** Accepted for this step
- **Date:** 2026-09-24
- **Context:** The lab cluster, VMware VMs, and host-only network already exist and are in use.
- **Decision:** The first repository change is files on the workstation only. No cluster, VM, or network change is part of repository bootstrap.
- **Consequences:** Application code, manifests, Terraform, Jenkins, and Argo CD arrive in later reviewed phases.

## Open decisions

| ID | Question | Notes |
|---|---|---|
| ADR-001 | Which container registry serves the local lab, and which serves AWS? | Choose before the first image publish. |
| ADR-002 | Where does Jenkins run? | Workstation, a VM, or the cluster. Undecided. |
| ADR-003 | Where does Argo CD run? | Likely in-cluster per target. Undecided. |
| ADR-004 | AWS footprint | Managed Kubernetes versus a self-managed cluster. Undecided. Terraform stays under `terraform/aws`. |
| ADR-005 | Image promotion | One image digest promoted between targets, or separate builds. Undecided. |
