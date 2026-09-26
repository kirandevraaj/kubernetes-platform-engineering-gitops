# Cost awareness (conceptual)

No fixed AWS list prices claimed here.

## Major cost drivers (AWS lab)

| Driver | Why it matters |
|---|---|
| EKS control plane | Hourly cluster charge |
| EC2 node groups | Primary compute |
| NAT Gateway | Egress path cost |
| Public IPv4 | Address charges where applicable |
| ALB | L7 load balancing |
| EBS | Persistent volumes + snapshots |
| Prometheus/Grafana | Continuous scrape/storage on nodes |
| Data transfer | Cross-AZ / internet |

## Lab choice: single NAT Gateway

**Cost-conscious lab decision** with reduced AZ egress resilience versus multi-NAT production patterns. Documented as scope tradeoff, not "best practice for production."

## Related

[production-gaps.md](../operations/production-gaps.md) · Terraform AWS modules
