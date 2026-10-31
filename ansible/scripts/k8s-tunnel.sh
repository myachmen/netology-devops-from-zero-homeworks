#!/usr/bin/env bash
set -euo pipefail

ssh -N \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -L 127.0.0.1:6443:127.0.0.1:6443 \
  k8s-control-1
