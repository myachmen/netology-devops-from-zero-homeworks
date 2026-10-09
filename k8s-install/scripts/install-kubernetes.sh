#!/usr/bin/env bash
set -euo pipefail

K8S_MINOR="v1.36"
K8S_PACKAGE_VERSION="1.36.5-1.1"

echo "=== Installing Kubernetes components on $(hostname) ==="

export DEBIAN_FRONTEND=noninteractive

# 1. Install prerequisites
apt-get update
apt-get install -y apt-transport-https ca-certificates curl gpg

# 2. Configure Kubernetes APT repository
install -d -m 0755 /etc/apt/keyrings

curl -fsSL \
  "https://pkgs.k8s.io/core:/stable:/${K8S_MINOR}/deb/Release.key" \
  | gpg --dearmor --yes \
      -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

chmod 0644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/${K8S_MINOR}/deb/ /" \
  > /etc/apt/sources.list.d/kubernetes.list

# Remove earlier repository configuration, if present
if [ -f /usr/share/keyrings/kubernetes-apt-keyring.gpg ]; then
    rm -f /usr/share/keyrings/kubernetes-apt-keyring.gpg
fi

# 3. Install pinned Kubernetes version
apt-get update

apt-mark unhold kubelet kubeadm kubectl 2>/dev/null || true

apt-get install -y \
  "kubelet=${K8S_PACKAGE_VERSION}" \
  "kubeadm=${K8S_PACKAGE_VERSION}" \
  "kubectl=${K8S_PACKAGE_VERSION}"

# 4. Prevent unintended upgrades
apt-mark hold kubelet kubeadm kubectl

# 5. Enable kubelet
systemctl enable kubelet

# 6. Verify installation
echo "=== Installed Kubernetes versions ==="
kubeadm version -o short
kubectl version --client
kubelet --version

echo "=== Kubernetes components installation completed successfully ==="