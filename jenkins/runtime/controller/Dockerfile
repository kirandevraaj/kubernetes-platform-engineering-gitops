# Jenkins 2.568.3 LTS, the current stable line on https://www.jenkins.io/download/
# Pinned tag, not the moving jenkins/jenkins:lts tag.
FROM jenkins/jenkins:2.568.3-lts-jdk21

COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
