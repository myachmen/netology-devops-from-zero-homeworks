#!/usr/bin/env bash
set -euo pipefail

echo "=== Preparing Kubernetes node: $(hostname) ==="

# 1. Disable swap
echo "[1/4] Disabling swap..."
swapoff -a

if grep -Eq '^[^#].*[[:space:]]swap[[:space:]]' /etc/fstab; then
    sed -i.bak '/^[^#].*[[:space:]]swap[[:space:]]/s/^/#/' /etc/fstab
fi

# 2. Load required kernel modules
echo "[2/4] Configuring kernel modules..."

cat > /etc/modules-load.d/k8s.conf <<'EOF'
overlay
br_netfilter
EOF

modprobe overlay
modprobe br_netfilter

# 3. Configure networking
echo "[3/4] Configuring sysctl..."

cat > /etc/sysctl.d/99-kubernetes.conf <<'EOF'
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
EOF

sysctl -p /etc/sysctl.d/99-kubernetes.conf

# 4. Verify configuration
echo "[4/4] Verifying configuration..."

if [ -n "$(swapon --noheadings --show)" ]; then
    echo "ERROR: Swap is still enabled"
    exit 1
fi

for module in overlay br_netfilter; do
    if ! lsmod | grep -q "^${module} "; then
        echo "ERROR: Kernel module ${module} is not loaded"
        exit 1
    fi
done

for parameter in \
    net.bridge.bridge-nf-call-iptables \
    net.bridge.bridge-nf-call-ip6tables \
    net.ipv4.ip_forward
do
    value=$(sysctl -n "$parameter")
    if [ "$value" != "1" ]; then
        echo "ERROR: ${parameter}=${value}, expected 1"
        exit 1
    fi
done

echo "=== Kubernetes node preparation completed successfully ==="
