# CI/CD flow

Status: planned. No Jenkins job exists yet.

## Intended flow

1. A change lands on the application branch.
2. Jenkins checks out the repository.
3. Jenkins runs the Python test suite.
4. Jenkins builds a container image and tags it with the commit SHA.
5. Jenkins publishes the image to the registry chosen for that target.
6. Jenkins updates the image reference in the GitOps path, or opens a change that does so.
7. Argo CD reconciles the cluster from Git. Jenkins does not run `kubectl apply` against a live cluster as the steady-state deploy step.

## Boundaries

- CI produces an artifact and a Git change.
- CD is GitOps. The desired state lives in `gitops/` and `kubernetes/`.
- The local lab and the AWS target use different registries, credentials, and GitOps applications.
- Pipeline files will be added under `jenkins/` in a later phase.
