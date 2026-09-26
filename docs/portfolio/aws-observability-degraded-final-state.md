# Known final-state limitation — AWS observability Degraded (2026-09-26)

**Status:** Documented · **Verified:** Yes (read-only diagnosis) · **Environment:** AWS

## Summary

Argo Application `platform-observability-aws` remains **Synced / Degraded** at Project 1 portfolio freeze.

## Exact findings

| Field | Value |
|---|---|
| Namespace | `observability` |
| Pending Pod | `grafana-74d6fddf68-sfgzm` (surge RS rotates under template churn; previously `grafana-7565c9dc8d-f7m46`) |
| Owner | Surge ReplicaSet ← Deployment `grafana` |
| Status | Pending · FailedScheduling (`Too many pods`) |
| Deployment desired replicas | **1** |
| Serving Pod | `grafana-7c54bd9475-ddw92` **2/2 Running** |
| Argo Application health | **Degraded** or **Progressing** (not Healthy) while surge cannot schedule |

## Desired-state relationship

Git/Argo desired Deployment replicas remain **1**. The Pending Pod is the **surge** replica from a stuck RollingUpdate, not an intentional second replica. The previous ReplicaSet still provides the Ready Pod Argo/users can use.

## Remediation decision

**No mutation applied** for portfolio freeze:

- Deleting the Pending Pod alone would recreate it under the same density constraint.
- Scaling nodes or deleting unrelated workloads would expand scope beyond documentation freeze.
- Changing Git strategy without capacity planning could disrupt the serving Grafana.

**Known final-state limitation:** observability Application reports Degraded while Grafana remains available (1 Ready). Application `/health`, storage, security, and core Argo apps are unaffected.

## Related

[grafana-unavailable.md](../runbooks/grafana-unavailable.md) · [known-limitations.md](../portfolio/known-limitations.md)
