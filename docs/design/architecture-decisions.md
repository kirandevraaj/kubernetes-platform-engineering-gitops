# Architecture decisions

Record a decision here when it is accepted. Until then, items below are open.

## ADR-000: Repository starts as documentation and layout

- **Status:** Accepted for this step
- **Date:** 2026-09-24
- **Context:** The lab cluster, VMware VMs, and host-only network already exist and are in use.
- **Decision:** The first repository change is files on the workstation only. No cluster, VM, or network change is part of repository bootstrap.
- **Consequences:** Application code, manifests, Terraform, Jenkins, and Argo CD arrive in later reviewed phases.

## ADR-003: Argo CD runs in the VMware lab cluster

- **Status:** Accepted
- **Date:** 2026-09-24
- **Context:** CD must reconcile `kubernetes/overlays/local` onto the existing three-node lab without using Docker Desktop Kubernetes or AWS.
- **Decision:** Install Argo CD `v3.5.3` into namespace `argocd` on context `ckad-lab`. Application destinations use the in-cluster server `https://kubernetes.default.svc` and namespace `platform-lab`. Sync policy is automated with prune and selfHeal.
- **Consequences:** Git is the desired-state source for the local overlay. Jenkins remains CI-only. A later AWS Application would be a separate object with a different destination.

## ADR-006: Jenkins stays off the deploy path

- **Status:** Accepted
- **Date:** 2026-09-24
- **Context:** The Jenkins pipeline already publishes `kirandevraaj/platform-lab:<APP_VERSION>` to Docker Hub.
- **Decision:** Jenkins does not run `kubectl apply` and does not talk to Argo CD for deploy. Image publish and cluster reconcile stay separate.
- **Consequences:** A new image tag becomes live only after Git records that tag in the Kubernetes manifests and Argo CD syncs.

## ADR-007: Observability uses kube-prometheus-stack with Grafana LoadBalancer

- **Status:** Accepted
- **Date:** 2026-09-24
- **Context:** The lab had no Prometheus Operator, Grafana, or ServiceMonitor CRDs. Application metrics needed a scrape path without changing MetalLB pool, ingress-nginx VIP `192.168.56.200`, or the AWS overlay.
- **Decision:** Install `kube-prometheus-stack` chart `91.5.1` into namespace `monitoring` via Argo CD Application `platform-lab-observability`. Prometheus Service stays ClusterIP. Grafana Service is LoadBalancer so MetalLB allocates another address from existing `lab-pool`. No Grafana Ingress. Application scrape uses ServiceMonitor in the local overlay; NetworkPolicy allows namespace `monitoring`. Alertmanager is disabled for a minimal footprint.
- **Consequences:** Grafana EXTERNAL-IP is discovered after reconcile and must not be hard-coded. AppProject `platform-lab` gains `ServiceMonitor` permission. Jenkins promotion updates only `newTag` so overlay resources (ingress Service patch, ServiceMonitor, patches) survive promotion.

## ADR-008: Local reliability uses HPA, PDB, and soft topology spread

- **Status:** Accepted
- **Date:** 2026-09-24
- **Context:** The local lab Deployment used implicit RollingUpdate defaults, had no HPA or PDB, and lacked explicit topology preferences. metrics-server is healthy. AWS overlay must stay unchanged.
- **Decision:** Add local-overlay only resources: HPA (`autoscaling/v2`, CPU 70%, min 2 / max 4), PDB (`minAvailable: 1`), RollingUpdate `maxUnavailable: 0` / `maxSurge: 1`, and `topologySpreadConstraints` with `ScheduleAnyway`. Do not add a startupProbe (FastAPI is fast to Ready). Argo CD ignores Deployment `/spec/replicas` so HPA can scale without sync fights.
- **Consequences:** Reliability objects live under `kubernetes/overlays/local`. AppProject gains HPA and PDB kinds. Idle CPU may keep HPA at minReplicas; that is an accepted lab limitation.

## Open decisions

| ID | Question | Notes |
|---|---|---|
| ADR-001 | Which container registry serves the local lab, and which serves AWS? | Local lab uses Docker Hub `kirandevraaj/platform-lab`. AWS registry undecided. |
| ADR-002 | Where does Jenkins run? | Accepted in practice: Docker Desktop on the workstation. Formal ADR can close later. |
| ADR-004 | AWS footprint | Managed Kubernetes versus a self-managed cluster. Undecided. Terraform stays under `terraform/aws`. |
| ADR-005 | Image promotion | One image digest promoted between targets, or separate builds. Undecided. |
