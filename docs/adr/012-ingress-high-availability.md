# ADR 012: Ingress high availability (VMware)

- **Status:** Accepted

## Context

Single ingress-nginx replica on one worker was a **SPOF** under worker failure experiments.

## Decision

Run ingress-nginx with **2 replicas**, topology spread across workers, and **PDB**.

## Consequences

Improved resilience; do **not** claim zero packet loss for every failure mode.

## Evidence

Commits `eb622e9` / `9228fef` · [vmware-ingress-spof.md](../postmortems/vmware-ingress-spof.md) · [ingress-unavailable.md](../runbooks/ingress-unavailable.md)
