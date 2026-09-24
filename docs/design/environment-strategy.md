# Environment strategy

Status: accepted as a constraint. Implementation of the AWS target has not started.

## Targets

| Name | Runtime | Kubernetes access | IaC |
|---|---|---|---|
| Local | VMware Workstation VMs `k8s-ctrl-01`, `k8s-worker-01`, `k8s-worker-02` | Context `ckad-lab`, nodes `192.168.56.10`–`.12` | None in this phase. The cluster already exists. |
| AWS | To be defined | A dedicated kube context, created only in the AWS phase | `terraform/aws` |

## Rules

- Local overlay values and AWS overlay values live in different directories.
- Terraform for AWS uses its own state and credentials. It does not describe the VMware VMs.
- GitOps Applications name their destination cluster explicitly.
- A kubectl context change is a deliberate step, checked before any future write command.
- Read-only inspection of the local cluster is allowed while documenting. Installs, upgrades, deletes, restarts, and network edits wait for approval.

## What "separate" means in practice

A local test uses the lab nodes and the local overlay. An AWS test uses the AWS account, the AWS overlay, and AWS state. Success in one environment is evidence for that environment only.
