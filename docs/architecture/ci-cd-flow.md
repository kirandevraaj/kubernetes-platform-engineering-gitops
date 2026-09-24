# CI/CD flow

Status: CI pipeline is defined in `jenkins/Jenkinsfile`. Jenkins is not installed or configured, and the pipeline has not run. CD is not implemented. No Argo CD Application exists yet.

## CI and CD

CI builds, tests, packages, and publishes an image. It stops at Docker Hub.

CD is a later phase. Argo CD is planned to reconcile Kubernetes from Git. This repository does not claim that Argo CD is installed or that it deploys the application.

Jenkins does not run `kubectl apply` as the deploy step.

## Intended CI path

```text
Developer
    |
    v
GitHub
    |
    v
Jenkins CI
    |-- Checkout
    |-- Unit Test
    |-- Read Application Version
    |-- Docker Build
    |-- Docker Image Validation
    |-- Docker Hub Push
            |
            v
      Docker Hub
      kirandevraaj/platform-lab:<APP_VERSION>
```

`APP_VERSION` is read from `app/src/__init__.py`. The current value is `0.1.0`, so the image name is `kirandevraaj/platform-lab:0.1.0`. The tag `latest` is not used.

The Docker Hub token is a Jenkins credential named `dockerhub-platform-lab`. It is not stored in Git. Creating that credential and running the job are still outstanding.

## What CI does not do

- It does not edit the live cluster.
- It does not install Argo CD.
- It does not update GitOps desired state. That remains a later step if a new image tag must be recorded in `kubernetes/`.
- It does not publish one image for the local lab and another for AWS. Both targets use the same versioned image name until an AWS registry is introduced.

## Later CD path

When that phase starts, a commit that changes the desired image reference in Git is the input. Argo CD is planned to render `kubernetes/overlays/local` or `kubernetes/overlays/aws` and converge the matching cluster. Those Applications do not exist yet. The local VMware workload that is already running was applied directly from the local overlay, not by this pipeline and not by Argo CD.
