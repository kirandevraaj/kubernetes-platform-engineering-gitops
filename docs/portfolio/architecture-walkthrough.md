# Architecture walkthrough

Left → right on [project1-reference-architecture.svg](../diagrams/project1-reference-architecture.svg):

1. **Developer** — changes code/manifests  
2. **GitHub** — source of truth for code + desired state  
3. **Jenkins** — owns CI; disappears → no new releases, runtime continues  
4. **Docker Hub** — artifacts; outage may block new pulls  
5. **Argo CD** — reconciles Git; pause → drift unrepaired until recovery  
6. **AppProject / Applications** — policy + desired workloads  
7. **VMware / AWS data planes** — serve traffic via VIP/ALB  
8. **Storage** — local-path vs EBS  
9. **Observability / automation / security / DR** — management planes, not user hops  

If a component disappears: classify blast radius using [platform-failure-domain.svg](../diagrams/platform-failure-domain.svg) and runbooks.
