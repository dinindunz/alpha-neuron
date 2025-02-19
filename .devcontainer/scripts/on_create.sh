#!/bin/bash

cat "$1/config.zsh" >> ~/.zshrc
# sudo echo 'DOCKER_OPTS="--iptables=false"' >> /etc/default/docker
# sudo chmod 666 /var/run/docker.sock
