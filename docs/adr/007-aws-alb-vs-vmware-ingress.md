# ADR 007: AWS ALB vs VMware ingress

- **Status:** Accepted

## Decision

- **VMware:** MetalLB L2 VIP (`192.168.56.200`) → ingress-nginx → Service → Pods  
- **AWS:** AWS Load Balancer Controller → **ALB** with **target-type ip** → Pod IP; health `/health`

## Rationale

Lab networks differ: on-prem L2 VIP vs AWS VPC/ALB native integration. Architectures are intentionally not identical.

## Evidence

[vmware-networking-anatomy.md](../vmware-networking-anatomy.md) · [aws-alb-unhealthy.md](../runbooks/aws-alb-unhealthy.md) · ADR [012](012-ingress-high-availability.md)
