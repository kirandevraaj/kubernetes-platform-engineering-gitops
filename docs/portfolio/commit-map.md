# Commit map — Project 1 narrative

Grouped themes from `git log --oneline`. SHAs are from repo history at Section 27 authoring; re-run `git log` after new work.

## How to use

- Interview: pick a theme → cite commit message → point to doc/evidence  
- Optional: add your own notes in **Your note** column later

---

## Foundation — app, CI, local GitOps

| SHA | Message | Theme |
|-----|---------|-------|
| e2c51a3 | fix: reach the CI health check through the agent network | Jenkins bootstrap |
| e2b7964 | chore: set APP_ENVIRONMENT to local-gitops for GitOps demo | GitOps config |
| 71ed15b | feat: add Argo CD GitOps for the local platform-lab overlay | Argo CD |
| e875218 | docs: record Argo CD GitOps sync and self-heal demos | Self-heal evidence |
| 0a633da | feat: automate Jenkins image publish and local GitOps promotion | CI→Git promotion |
| 5b2ce38 | docs: record automated CI/CD promotion of platform-lab 0.1.2 | CI/CD doc |

## Ingress, network policy, MetalLB

| SHA | Message | Theme |
|-----|---------|-------|
| 99a0f98 | feat: add ingress and network policy for platform-lab | Net + NP |
| bfeb721 | feat: expose local ingress-nginx through MetalLB | MetalLB |
| e0403cd | docs: record MetalLB LoadBalancer VIP for local ingress-nginx | Doc |

## Observability

| SHA | Message | Theme |
|-----|---------|-------|
| 1c562fc | feat: add Prometheus/Grafana observability for platform-lab | Obs stack |
| a3ee50f | fix: raise Grafana memory limit to stop OOMKills | Grafana OOM |
| 7572cfe | feat: add kubernetes platform observability | Platform obs |
| c269238 | feat: add cross-environment platform sre dashboards | Dashboards |

## Reliability (HPA, PDB)

| SHA | Message | Theme |
|-----|---------|-------|
| bc8181f | feat: harden local platform-lab with HPA, PDB, and safe rollouts | Reliability |
| be72ebf | docs: record local reliability validation for platform-lab | Evidence |

## Failed rollout 0.1.5 lab

| SHA | Message | Theme |
|-----|---------|-------|
| 0c4fe12 | feat: release 0.1.5 with intentional VMware readiness failure | Inject failure |
| 6acbe3e | chore: promote platform-lab 0.1.5 digest to local and aws GitOps | Bad promote |
| 302a506 | fix: rollback platform-lab overlays to known-good 0.1.4 digest | Rollback |
| 95820c8 | revert: restore healthy 0.1.4 application source after readiness-failure lab | Recovery |

## Ingress HA & VMware resilience docs

| SHA | Message | Theme |
|-----|---------|-------|
| eb622e9 | feat: make vmware ingress highly available | Ingress HA |
| 675586c | fix: drop Force sync option incompatible with ServerSideApply | Argo sync |
| 9228fef | docs: record vmware ingress-nginx HA validation | Evidence |
| 84c3478 | docs: document vmware node failure resilience | Node failure |

## AWS platform & GitOps

| SHA | Message | Theme |
|-----|---------|-------|
| 0ea6f13 | chore: prepare aws terraform tooling foundation | TF foundation |
| 5e304cd | feat: add aws eks terraform platform | EKS |
| 5da676f | feat: pin gitops releases by image digest | Digest pin |
| baf74d5 | chore: promote platform-lab 0.1.4 to local and aws GitOps | 0.1.4 pin |
| 0590eb7 | release: platform-lab 0.1.4 | Release |

## AWS storage & resilience

| SHA | Message | Theme |
|-----|---------|-------|
| bd5e6dc | feat: add aws ebs storage lab | EBS lab |
| c8d45ca | feat: validate aws ebs node failure resilience | ~6.3 min recovery |

## Security

| SHA | Message | Theme |
|-----|---------|-------|
| 85d76a6 | feat: add kubernetes security and rbac hardening | Security lab |
| 2525408 | docs: document kubernetes security and rbac hardening | Doc |

## Advanced Argo

| SHA | Message | Theme |
|-----|---------|-------|
| 6d57e42 | feat: add advanced argo cd gitops patterns | Advanced GitOps |
| 7a1369a | feat: add syncfail and health-wave demo applications | Waves/syncfail |

## Automation

| SHA | Message | Theme |
|-----|---------|-------|
| 5593a26 | feat: add platform automation framework | Python/Ansible |
| 0436b0c | docs: fix automation diagram encoding | Doc |

## Disaster recovery & operations

| SHA | Message | Theme |
|-----|---------|-------|
| 2a013bd | feat: add disaster recovery and restore lab | DR lab |
| e4d61be | docs: record DR lab evidence and fix storage AppProject whitelist | DR evidence |
| 87b3034 | docs: align DR tested status with measured lab evidence | DR honesty |
| 8e09fd7 | feat: add platform operations handbook and runbooks | Section 26 ops |

---

## Placeholder — Section 27 portfolio commits

| SHA | Message | Theme |
|-----|---------|-------|
| _TBD_ | docs: add Section 27 portfolio packaging | Portfolio |

---

**Regenerate:** `git log --oneline -100` from repo root.
