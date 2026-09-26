# ADR 005: Kustomize for environment overlays

- **Status:** Accepted

## Context

Shared app base with VMware vs AWS differences (ingress, env, resources).

## Decision

**Kustomize** base + `overlays/local` and `overlays/aws`.

## Note

This does not claim Kustomize is always preferable to Helm. Helm is used where charts fit (e.g. observability stacks).

## Evidence

`kubernetes/base` · `kubernetes/overlays/*`
