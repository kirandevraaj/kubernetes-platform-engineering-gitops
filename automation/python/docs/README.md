# Platform automation docs

Lab-only Python package under `automation/python`.

## Modules

| Area | Purpose |
|------|---------|
| `cli` | `platform-automate` entry point |
| `controller` | DI orchestration discover/validate/plan/apply/verify/report |
| `kubernetes` | read + lab-scoped mutations in `automation-lab` |
| `aws` | read-only discovery + allowlisted tags |
| `ansible` | playbook runner with Windows subprocess fallback |
| `rest` | `ApiClient` with timeout/retry |
| `terraform` | plan-only wrapper; guarded apply |

## Reports

JSON reports write to `automation/reports/` (gitignored).

## GitOps

Desired state for the demo stack lives in `kubernetes/automation-lab/`.
Optional Argo Application: `gitops/applications/automation-lab.yaml` (manual sync / prune=false).
