# Registry Unavailable (Docker Hub / remote registry)

## Impact (architecture-based; avoid overclaim)
- Existing Pods may continue with **cached** images on nodes.  
- New Pod scheduling may fail if image is not present locally.  
Exact eviction/pull behavior under prolonged outage: **Not tested as a dedicated Project 1 drill.**

## Mitigation (Design guidance)
Registry availability; artifact retention; replication/mirroring; pin digests already pulled.

## Related
[docker-release-failure.md](./docker-release-failure.md) · [production-gaps.md](../operations/production-gaps.md)
