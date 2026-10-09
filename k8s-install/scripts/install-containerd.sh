
#!/usr/bin/env bash
set -euo pipefail

echo "=== Installing containerd on $(hostname) ==="

export DEBIAN_FRONTEND=noninteractive

# Install containerd from Ubuntu repositories
apt-get update
apt-get install -y containerd

# Generate configuration for the installed version
mkdir -p /etc/containerd

if [ ! -f /etc/containerd/config.toml ]; then
    containerd config default > /etc/containerd/config.toml
fi

# Detect containerd configuration version
CONFIG_VERSION=$(containerd config dump | grep -m1 '^version = ' || true)

echo "Containerd configuration: ${CONFIG_VERSION}"

# Configure systemd cgroups for containerd 1.x or 2.x
if grep -q 'SystemdCgroup = false' /etc/containerd/config.toml; then
    sed -i 's/SystemdCgroup = false/SystemdCgroup = true/g' \
        /etc/containerd/config.toml
fi

# Ensure CRI is not disabled
if grep -Eq '^disabled_plugins[[:space:]]*=' /etc/containerd/config.toml; then
    sed -i '/^disabled_plugins[[:space:]]*=/s/"cri"//g' \
        /etc/containerd/config.toml
fi

systemctl enable --now containerd
systemctl restart containerd

echo "=== Verifying containerd ==="

containerd --version
systemctl is-active --quiet containerd

if ! grep -q 'SystemdCgroup = true' /etc/containerd/config.toml; then
    echo "ERROR: SystemdCgroup is not enabled"
    exit 1
fi

echo "=== Containerd installation completed successfully ==="
