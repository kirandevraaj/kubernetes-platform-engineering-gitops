# Remoting image that matches the current jenkins/inbound-agent:jdk21 line.
# Pin the remoting tag. Do not use the moving latest-jdk21 tag.
FROM jenkins/inbound-agent:3391.va_37fa_a_305d6d-3-jdk21

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        python3 \
        python3-pip \
        python3-venv \
    && curl -fsSL https://download.docker.com/linux/static/stable/x86_64/docker-29.6.1.tgz \
        | tar -xz -C /usr/local/bin --strip-components=1 docker/docker \
    && ln -sf "$(command -v pip3)" /usr/local/bin/pip \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/platform-lab-agent-entrypoint
RUN chmod 755 /usr/local/bin/platform-lab-agent-entrypoint

ENTRYPOINT ["/usr/local/bin/platform-lab-agent-entrypoint"]
