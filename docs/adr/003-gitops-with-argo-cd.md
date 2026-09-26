# ADR 003: GitOps with Argo CD

- **Status:** Accepted

## Context

Need continuous reconciliation and a single desired-state source after CI.

## Decision

**Git** stores desired Kubernetes state; **Argo CD** reconciles each environment (separate installations on VMware and AWS). **Jenkins** builds/promotes; it does **not** `kubectl apply` as the primary CD path.

## Why not Jenkins kubectl deploy

Imperative deploys diverge from Git, weaken auditability, and fight Argo selfHeal. Project 1 prefers: Jenkins → digest in Git → Argo sync.

## Evidence

Argo v3.5.3 / v3.1.0 · selfHeal ~6s lab · [argo-advanced-patterns.md](../argo-advanced-patterns.md)
