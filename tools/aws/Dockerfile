# Isolated Ubuntu LTS workstation for AWS / Terraform / Kubernetes CLIs.
# No credentials, kubeconfigs, or Terraform state are baked into this image.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PATH="/usr/local/bin:${PATH}"

WORKDIR /tmp

RUN apt-get -o Acquire::Retries=5 update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        unzip \
        git \
        jq \
        lsb-release \
        software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# --- AWS CLI v2 (official installer) ---
RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip \
    && unzip -q awscliv2.zip \
    && ./aws/install \
    && rm -rf awscliv2.zip aws \
    && aws --version

# --- HashiCorp apt repository + Terraform ---
RUN curl -fsSL https://apt.releases.hashicorp.com/gpg \
        | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" \
        > /etc/apt/sources.list.d/hashicorp.list \
    && apt-get -o Acquire::Retries=5 update \
    && apt-get install -y --no-install-recommends terraform \
    && rm -rf /var/lib/apt/lists/* \
    && terraform version

# --- kubectl (official Kubernetes release binary; client for EKS 1.36) ---
# Version skew: kubectl client should stay within one minor of the cluster.
# Uses dl.k8s.io stable-1.36 channel rather than the Ubuntu package mirrors.
RUN KUBECTL_VERSION="$(curl -fsSL https://dl.k8s.io/release/stable-1.36.txt)" \
    && curl -fsSLo /usr/local/bin/kubectl "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
    && chmod +x /usr/local/bin/kubectl \
    && kubectl version --client

# --- Helm (official install script) ---
RUN curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash \
    && helm version

WORKDIR /workspace

CMD ["bash"]
