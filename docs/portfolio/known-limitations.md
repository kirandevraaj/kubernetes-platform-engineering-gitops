# Known limitations

| Item | Current project | Production enhancement |
|---|---|---|
| AWS observability Degraded (Grafana Pending / Too many pods) | Documented freeze state; Grafana 1/1 Ready | More node capacity or roll strategy tuning |
| AWS NetworkPolicy enforcement | Objects exist; enforcement not observed | Validate CNI policy enforcement |
| Windows Ansible CLI | Blocked | Linux runners / AWX |
| Live Boto3 on Windows workstation | Limited | Execute via Linux/CI |
| AWS Backup EKS restore | Assessed only | Execute & document restore |
| Full EKS rebuild | Not destructively tested | Controlled rebuild drill |
| Cross-region DR | Not implemented | Multi-region design |
| EBS AZ boundary | Observed | Multi-AZ data strategy |
| Centralized alerting/on-call | Not implemented | Alertmanager + paging |
| Production secret manager | Not implemented | External secrets / KMS |
| Remote Terraform backend | Not implemented | S3+DynamoDB locking |

Frame as **scope boundaries**, not project failures.
