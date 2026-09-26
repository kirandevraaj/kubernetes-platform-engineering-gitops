# Operations Interview Notes (Section 26)

Answers reference **Observed in Project 1** where applicable.

1. **What does a good Kubernetes runbook contain?**  
   Symptoms, impact, severity, first 60s READ-ONLY checks, evidence, triage, safe remediation, verification, rollback, escalation, Do-Not-Do, observed lab results, links — see [runbook-template.md](../runbooks/runbook-template.md).

2. **How do you triage a production Kubernetes incident?**  
   Classify layer → blast radius → health state → recent changes → evidence → smallest safe change → verify ([triage-framework.md](../troubleshooting/triage-framework.md)).

3. **What do you check first when an application returns 503?**  
   Ingress/ALB health → Endpoints/EndpointSlices → Pod Ready → Deployment → Argo → recent Git/Jenkins ([application-unhealthy.md](../runbooks/application-unhealthy.md)).

4. **Application vs ingress vs Service?**  
   Walk failure domain: VIP/ALB → Ingress → Service → Endpoints → Pod ([platform-failure-domain.svg](../diagrams/platform-failure-domain.svg)).

5. **Pending Pods?**  
   Events, scheduling, PVC/EBS attach, image pull, resources, taints ([pvc-pv-troubleshooting.md](../runbooks/pvc-pv-troubleshooting.md), [ebs-attach-troubleshooting.md](../runbooks/ebs-attach-troubleshooting.md)).

6. **NotReady Pods?**  
   Running ≠ Ready; readiness probe; endpoints drop; RS may **not** replace ([pod-not-ready.md](../runbooks/pod-not-ready.md)).

7. **Argo ComparisonError?**  
   Source generation (lab: missing `../base/namespace.yaml`) → Unknown until kustomize fixed ([argo-comparison-error.md](../postmortems/argo-comparison-error.md)).

8. **GitOps rollback?**  
   Identify known-good commit/digest (`0.1.4`) → Git revert → Argo reconcile — not primary `kubectl rollout undo` ([failed-rollout-0.1.5.md](../postmortems/failed-rollout-0.1.5.md)).

9. **EBS attach failures?**  
   VolumeAttachment, CSI, AZ, `FailedAttachVolume` events; do not manual attach ([ebs-attach-troubleshooting.md](../runbooks/ebs-attach-troubleshooting.md)).

10. **HPA not scaling?**  
    Metrics Server, requests, HPA events; lab scaled VMware 2→4, AWS 2→3 ([hpa-not-scaling.md](../runbooks/hpa-not-scaling.md)).

11. **Prometheus target failures?**  
    ServiceMonitor labels, `/metrics`, Endpoints, NetworkPolicy; separate control-plane scrape noise ([prometheus-target-down.md](../runbooks/prometheus-target-down.md)).

12. **RBAC denied?**  
    Who/what/where → Role → Binding → `kubectl auth can-i` before grants ([rbac-access-denied.md](../runbooks/rbac-access-denied.md)).

13. **Worker-node failure?**  
    VMware kubelet NotReady vs AWS terminate + same-AZ EBS ~6.3 min ([worker-node-failure.md](../runbooks/worker-node-failure.md)).

14. **Measure RTO?**  
    T0 detect … Tn recovered; lab examples in [rpo-rto-operational-guide.md](./rpo-rto-operational-guide.md) — not SLA.

15. **Measure RPO?**  
    Last consistent restore point (e.g. snapshot POINT-A) vs data loss window — lab measured snapshot timings, not org RPO contract.

16. **Evidence?**  
    Context, Git SHA, digest, pods, events, metrics — never Secret values ([incident-evidence.md](./incident-evidence.md)).

17. **What makes a good runbook?**  
    Quality gate Phase 67: identifiable symptom, safe commands, verify, rollback, escalation, observed results.

18. **Never automate blindly?**  
    Destroy, EBS detach, cluster-admin grants, secret printing, blind terraform apply.

19. **Avoid making incidents worse?**  
    Evidence first; stabilize; smallest change; escalate instead of risky experiments ([escalation.md](./escalation.md)).

20. **Postmortem → improvement?**  
    Detection, automation, runbook, permanent fix action items ([postmortem-template.md](../postmortems/postmortem-template.md)).
