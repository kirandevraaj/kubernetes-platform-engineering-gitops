#!/bin/bash
set -eu

socket=/var/run/docker.sock
if [ -S "${socket}" ]; then
    gid="$(stat -c '%g' "${socket}")"
    if ! getent group "${gid}" >/dev/null; then
        groupadd --gid "${gid}" dockerhost
    fi
    group_name="$(getent group "${gid}" | cut -d: -f1)"
    usermod -aG "${group_name}" jenkins
fi

exec runuser -u jenkins -- /usr/local/bin/jenkins-agent "$@"
