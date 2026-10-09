#!/usr/bin/env bash
set -euo pipefail

echo "=== Configuring kubelet node IP ==="

NODE_IP=$(ip -4 -o addr show dev eth1 | awk '{print $4}' | cut -d/ -f1)

if [[ -z "$NODE_IP" ]]; then
    echo "ERROR: Cannot determine IP address of eth1"
    exit 1
fi

echo "Detected node IP: $NODE_IP"

printf 'KUBELET_EXTRA_ARGS="--node-ip=%s"\n' "$NODE_IP" \
    > /etc/default/kubelet

systemctl daemon-reload
systemctl restart kubelet

echo "=== Kubelet configured successfully ==="