# ADR 010: Python and Ansible automation boundary

- **Status:** Accepted

## Decision

| Tool | Owns |
|---|---|
| Terraform | Infrastructure lifecycle |
| Python | Custom logic, APIs, CLI (`platform-automate`) |
| Boto3 | AWS API calls from Python |
| Ansible | Config / operational orchestration (Linux/Jenkins) |
| Argo CD | GitOps reconciliation |
| Jenkins | CI orchestration |

Tools are **not interchangeable**. Windows Ansible CLI is **blocked** in this project.

## Evidence

[platform-automation-master-guide.md](../automation/platform-automation-master-guide.md) · [tool-boundaries.md](../architecture/tool-boundaries.md)
