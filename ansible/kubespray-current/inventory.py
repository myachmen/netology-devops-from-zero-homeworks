#!/usr/bin/env python3
"""Local inventory reader; never contacts cloud APIs or remote hosts."""
import argparse
import ipaddress
import json
import os
from pathlib import Path
import shlex
import stat
import sys

NAMES = ("k8s-control-1", "k8s-worker-1", "k8s-worker-2")
BASE = Path(__file__).resolve().parent


def inventory():
    source = BASE / ".local" / "nodes.json"
    info = source.lstat()
    parent = source.parent.lstat()
    if not (stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o600
            and stat.S_ISDIR(parent.st_mode)
            and stat.S_IMODE(parent.st_mode) == 0o700):
        raise ValueError("Local settings must be owner-only regular file in private directory")
    data = json.loads(source.read_text())
    if set(data["hosts"]) != set(NAMES):
        raise ValueError("Unexpected host set")
    trust = Path(data["known_hosts_file"])
    key = Path(data["ssh_private_key_file"])
    for path in (trust, key):
        entry = path.lstat()
        if not (stat.S_ISREG(entry.st_mode) and entry.st_uid == os.getuid()
                and stat.S_IMODE(entry.st_mode) == 0o600):
            raise ValueError("SSH files must be existing owner-only regular files")
    args = ["-F", str(BASE / "ssh_config"),
            "-o", "UserKnownHostsFile=" + str(trust),
            "-o", "GlobalKnownHostsFile=" + str(trust),
            "-o", "StrictHostKeyChecking=yes", "-o", "HostKeyAlgorithms=ssh-ed25519",
            "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
            "-o", "ForwardAgent=no", "-o", "UpdateHostKeys=no",
            "-o", "ConnectionAttempts=1", "-o", "ConnectTimeout=10"]
    hosts = {}
    for name in NAMES:
        item = data["hosts"][name]
        for field in ("public_endpoint", "private_endpoint"):
            if ipaddress.ip_address(item[field]).version != 4:
                raise ValueError("Expected IPv4 endpoint")
        hosts[name] = {
            "ansible_host": item["public_endpoint"],
            "ip": item["private_endpoint"], "access_ip": item["private_endpoint"],
            "ansible_user": "ubuntu", "ansible_become": True,
            "ansible_become_method": "sudo", "ansible_become_user": "root",
            "ansible_become_flags": "-H -S -n",
            "ansible_python_interpreter": "/usr/bin/python3",
            "ansible_ssh_private_key_file": str(key),
            "ansible_ssh_common_args": shlex.join(args),
            "ansible_host_key_checking": True,
        }
    return {
        "_meta": {"hostvars": hosts},
        "all": {"children": ["k8s_cluster", "etcd", "calico_rr", "ungrouped"]},
        "kube_control_plane": {"hosts": ["k8s-control-1"]},
        "etcd": {"hosts": ["k8s-control-1"]},
        "kube_node": {"hosts": ["k8s-worker-1", "k8s-worker-2"]},
        "k8s_cluster": {"children": ["kube_control_plane", "kube_node"]},
        "calico_rr": {"hosts": []}, "ungrouped": {"hosts": []},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true")
    mode.add_argument("--host")
    args = parser.parse_args()
    try:
        result = inventory()
        print(json.dumps(result if args.list else result["_meta"]["hostvars"].get(args.host, {})))
    except (OSError, ValueError, KeyError, TypeError):
        print("Inventory unavailable: validate private local settings and existing SSH trust", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
