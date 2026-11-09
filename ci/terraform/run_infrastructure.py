#!/usr/bin/env python3
"""Future trusted-diploma-branch entry point. NOT authorized to execute in task 156.

No work at import time. Every process is foreground; no retry or rollback.
This remains unreachable from GitHub Actions until separately approved activation.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from plan_policy import evaluate, unique_object, reject_constant

REPOSITORY = "myachmen/netology-devops-from-zero-homeworks"
ACTIVATION = "OWNER_APPROVED_EXISTING_NOOP"
FINGERPRINTS = {
    "backend.tf": "865feaaf353b60a1a2598f950f3ba1e4d52d78e564b8961950c57707944b125d",
    ".terraform.lock.hcl": "6892204e30e8dcef9161324eab15bb8903850584a82b7d11ea3f9a66ce4181de",
}


class Stop(Exception):
    pass


def guard(env):
    if (env.get("TF_CI_ACTIVATION") != ACTIVATION
            or env.get("GITHUB_REPOSITORY") != REPOSITORY
            or env.get("GITHUB_EVENT_NAME") != "push"
            or env.get("GITHUB_REF") != "refs/heads/diplom-yandexcloud"
            or not re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))):
        raise Stop("TRUST_OR_ACTIVATION_GATE")
    forbidden = ("TF_CLI_ARGS", "TF_LOG", "TF_REATTACH_PROVIDERS")
    if any(any(k.startswith(prefix) for prefix in forbidden) for k in env):
        raise Stop("UNEXPECTED_TERRAFORM_ENV")
    if any(k in env for k in ("TF_CLI_CONFIG_FILE", "TF_DATA_DIR", "TF_PLUGIN_CACHE_DIR",
                              "AWS_PROFILE", "AWS_SHARED_CREDENTIALS_FILE",
                              "AWS_SESSION_TOKEN", "YC_TOKEN")):
        raise Stop("UNEXPECTED_CREDENTIAL_OR_CONFIG_ENV")
    names = ("TF_YC_SERVICE_ACCOUNT_KEY_JSON", "TF_S3_ACCESS_KEY_ID",
             "TF_S3_SECRET_ACCESS_KEY", "TF_VAR_cloud_id", "TF_VAR_folder_id",
             "TF_VAR_admin_cidr", "TF_SSH_PUBLIC_KEY", "GITHUB_TOKEN")
    if any(not env.get(name, "").strip() for name in names):
        raise Stop("MISSING_APPROVED_INPUT")


def current_trusted_branch(env):
    request = urllib.request.Request(
        "https://api.github.com/repos/" + REPOSITORY + "/git/ref/heads/diplom-yandexcloud",
        headers={"Authorization": "Bearer " + env["GITHUB_TOKEN"],
                 "Accept": "application/vnd.github+json", "User-Agent": "terraform-ci-gate"})
    with urllib.request.urlopen(request, timeout=20) as response:
        sha = json.load(response)["object"]["sha"]
    if sha != env["GITHUB_SHA"]:
        raise Stop("STALE_MAIN_SHA")


def run(command, root, env, destination, timeout, allowed=(0,)):
    with destination.open("wb") as stream:
        result = subprocess.run(command, cwd=root, env=env, stdout=stream,
                                stderr=subprocess.STDOUT, timeout=timeout, check=False)
    if result.returncode not in allowed:
        raise Stop("COMMAND_FAILED_OUTCOME_REQUIRES_REVIEW")
    return result.returncode


def execute():
    env = dict(os.environ)
    guard(env)  # Must precede filesystem credentials, any subprocess or network.
    repository = Path(__file__).resolve().parents[2]
    root = repository / "terraform" / "infrastructure"
    for name, digest in FINGERPRINTS.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise Stop("BACKEND_OR_LOCK_MISMATCH")
    # Exact provider lock/backend bytes are checked before any initialization.
    key = json.loads(env["TF_YC_SERVICE_ACCOUNT_KEY_JSON"], object_pairs_hook=unique_object)
    if not isinstance(key, dict) or not all(key.get(n) for n in ("id", "service_account_id", "private_key")):
        raise Stop("PROVIDER_KEY_SCHEMA")
    public_key = env["TF_SSH_PUBLIC_KEY"].strip()
    if "PRIVATE KEY" in public_key or "\n" in public_key or not public_key.startswith("ssh-ed25519 "):
        raise Stop("PUBLIC_KEY_CONTRACT")
    os.umask(0o077)
    with tempfile.TemporaryDirectory(prefix="terraform-ci-") as temp:
        private = Path(temp)
        provider_key = private / "provider.json"
        provider_key.write_text(json.dumps(key), encoding="utf-8")
        ssh_key = private / "existing.pub"
        ssh_key.write_text(public_key + "\n", encoding="utf-8")
        env.update({"YC_SERVICE_ACCOUNT_KEY_FILE": str(provider_key),
                    "AWS_ACCESS_KEY_ID": env.pop("TF_S3_ACCESS_KEY_ID"),
                    "AWS_SECRET_ACCESS_KEY": env.pop("TF_S3_SECRET_ACCESS_KEY"),
                    "TF_VAR_ssh_public_key_path": str(ssh_key),
                    "TF_WORKSPACE": "default", "TF_IN_AUTOMATION": "1", "TF_INPUT": "0"})
        for name in ("TF_YC_SERVICE_ACCOUNT_KEY_JSON", "TF_SSH_PUBLIC_KEY"):
            env.pop(name, None)
        if any(root.glob("*.auto.tfvars*")) or (root / "terraform.tfvars").exists() or (root / "terraform.tfvars.json").exists():
            raise Stop("UNREVIEWED_VARIABLE_FILE")
        current_trusted_branch(env)
        run(["git", "rev-parse", "HEAD"], repository, env, private / "head", 30)
        if (private / "head").read_text().strip() != env["GITHUB_SHA"]:
            raise Stop("CHECKOUT_SHA_MISMATCH")
        run(["terraform", "version", "-json"], root, env, private / "version.json", 30)
        if json.loads((private / "version.json").read_text()).get("terraform_version") != "1.15.7":
            raise Stop("CLI_VERSION")
        commands = [
            (["terraform", "fmt", "-check", "-recursive"], "fmt", 60),
            (["terraform", "init", "-input=false", "-lockfile=readonly", "-no-color"], "init", 180),
            (["terraform", "validate", "-no-color"], "validate", 120),
        ]
        for command, stage, timeout in commands:
            run(command, root, env, private / (stage + ".log"), timeout)
            print(stage + ": PASS")
        plan_file = private / "approved.tfplan"
        run(["terraform", "plan", "-input=false", "-no-color", "-refresh=true",
             "-lock=true", "-lock-timeout=60s", "-detailed-exitcode", "-out=" + str(plan_file)],
            root, env, private / "plan.log", 600, allowed=(0, 2))
        # Separate stderr: JSON must not be combined with warnings.
        with (private / "plan.json").open("wb") as output, (private / "show.log").open("wb") as error:
            result = subprocess.run(["terraform", "show", "-json", str(plan_file)], cwd=root,
                                    env=env, stdout=output, stderr=error, timeout=120, check=False)
        if result.returncode:
            raise Stop("PLAN_JSON_FAILED")
        plan = json.loads((private / "plan.json").read_text(), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
        summary = evaluate(plan)
        print(json.dumps(summary, sort_keys=True))
        plan_digest = hashlib.sha256(plan_file.read_bytes()).hexdigest()
        current_trusted_branch(env)
        if hashlib.sha256(plan_file.read_bytes()).hexdigest() != plan_digest:
            raise Stop("PLAN_FILE_CHANGED")
        run(["terraform", "apply", "-input=false", "-no-color", "-lock=true",
             "-lock-timeout=60s", str(plan_file)], root, env, private / "apply.log", 900)
        print("SAVED_NOOP_APPLY_EXIT_0; workload health requires separately scoped postchecks")


def main():
    try:
        execute()
        return 0
    except Exception:
        # Includes timeout/network/schema/permission failures. Do not print raw
        # subprocess logs or exception text; do not retry any operation here.
        print("STOP: GATE_OR_COMMAND_FAILURE; review outcome before any new run", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
