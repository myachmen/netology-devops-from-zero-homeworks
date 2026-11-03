#!/usr/bin/env python3
"""Pinned project environment; command line exposes offline checks only."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

PIN = "0c6a29553f90c55cba5e0e359470321dc7cf7d29"
BASE = Path(__file__).resolve().parent


def environment():
    checkout = Path(os.environ["KUBESPRAY_CHECKOUT"]).resolve()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()
    if git("rev-parse", "HEAD") != PIN or git("status", "--porcelain"):
        raise ValueError("Kubespray must be the clean pinned v2.29.1 checkout")
    env = os.environ.copy()
    env.update({
        "ANSIBLE_CONFIG": str(BASE.parent / "kubespray-current" / "ansible.cfg"),
        "ANSIBLE_INVENTORY": str(BASE / "inventory.py"),
        "ANSIBLE_ROLES_PATH": str(checkout / "roles"),
        "ANSIBLE_LIBRARY": str(checkout / "plugins" / "modules"),
        "ANSIBLE_HOST_KEY_CHECKING": "True",
    })
    # Caller must use this environment for any future separately authorised run.
    return checkout, env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "inventory-list", "inventory-graph", "config"))
    mode = parser.parse_args().mode
    checkout, env = environment()
    if mode == "verify":
        # A fresh interpreter is required: Ansible constants are read at import time.
        code = '''
import os
from pathlib import Path
from ansible.parsing.dataloader import DataLoader
from ansible.playbook.role.definition import RoleDefinition
from ansible.plugins.loader import module_loader
loader = DataLoader()
loader.set_basedir(os.environ["CHECKOUT"] + "/playbooks")
role = RoleDefinition(loader=loader)
name, path = role._load_role_path("kubespray_defaults")
assert Path(path).resolve() == Path(os.environ["CHECKOUT"]) / "roles/kubespray_defaults"
module = module_loader.find_plugin("kube", mod_type=".py")
assert Path(module).resolve() == Path(os.environ["CHECKOUT"]) / "plugins/modules/kube.py"
print("PASS: imported-playbook role lookup and custom kube module discovery")
'''
        env["CHECKOUT"] = str(checkout)
        return subprocess.call([sys.executable, "-c", code], env=env, cwd=BASE)
    executable = Path(sys.executable).parent / ("ansible-config" if mode == "config" else "ansible-inventory")
    args = ["dump", "--only-changed"] if mode == "config" else ["--list" if mode == "inventory-list" else "--graph"]
    return subprocess.call([str(executable), *args], env=env, cwd=BASE)


if __name__ == "__main__":
    sys.exit(main())
