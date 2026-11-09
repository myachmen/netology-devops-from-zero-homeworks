#!/usr/bin/env python3
"""Future owner-approved manual plan check. No execution authorized in task 159.

Independent of the apply runner. Only the five fixed Terraform commands below
are reachable. No import-time work, retry, state command, or artifact upload.
"""

import base64
import hashlib
import ipaddress
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from plan_policy import Denied, MAX_BYTES, evaluate, reject_constant, unique_object

REPOSITORY = "myachmen/netology-devops-from-zero-homeworks"
CLI_VERSION = "1.15.7"
APPROVAL_MARKER = "OWNER_APPROVED_PLAN_ONLY"
FINGERPRINTS = {
    "backend.tf": "865feaaf353b60a1a2598f950f3ba1e4d52d78e564b8961950c57707944b125d",
    ".terraform.lock.hcl": "6892204e30e8dcef9161324eab15bb8903850584a82b7d11ea3f9a66ce4181de",
}
REQUIRED = frozenset({"TF_PLAN_ACTIVATION", "TF_PLAN_APPROVED_SHA",
    "TF_YC_SERVICE_ACCOUNT_KEY_JSON", "TF_S3_ACCESS_KEY_ID", "TF_S3_SECRET_ACCESS_KEY",
    "TF_VAR_cloud_id", "TF_VAR_folder_id", "TF_VAR_admin_cidr", "TF_SSH_PUBLIC_KEY"})
CATEGORIES = frozenset({"TRUST_GATE", "INPUT_GATE", "ENV_OVERRIDE", "PUBLIC_KEY",
    "PROVIDER_KEY", "SOURCE_OR_BACKEND", "MAIN_METADATA", "STALE_MAIN", "COMMAND_FAILED",
    "COMMAND_TIMEOUT", "CLI_VERSION", "PLAN_JSON", "POLICY_DENIED", "NON_NOOP_EXIT",
    "LOCAL_IO_OR_SCHEMA", "UNEXPECTED_FAILURE"})


class Stop(Exception):
    def __init__(self, category, stage=None, returncode=None):
        super().__init__(category)
        self.stage = stage
        self.returncode = returncode


def gate(env):
    if (env.get("TF_PLAN_ACTIVATION") != APPROVAL_MARKER
            or env.get("GITHUB_REPOSITORY") != REPOSITORY
            or env.get("GITHUB_EVENT_NAME") != "workflow_dispatch"
            or env.get("GITHUB_REF") != "refs/heads/diplom-yandexcloud"
            or env.get("GITHUB_RUN_ATTEMPT") != "1"
            or not re.fullmatch(r"[0-9a-f]{40}", env.get("GITHUB_SHA", ""))
            or env.get("GITHUB_SHA") != env.get("TF_PLAN_APPROVED_SHA")):
        raise Stop("TRUST_GATE")
    if any(not isinstance(env.get(k), str) or not env[k].strip() for k in REQUIRED):
        raise Stop("INPUT_GATE")
    if not env.get("GITHUB_TOKEN"):
        raise Stop("INPUT_GATE")
    # Permit only the declared contract; in particular no CLI args/log/config,
    # workspace, alternate provider token, endpoint, profile or variable override.
    if any((k.startswith("TF_") and k not in REQUIRED)
           or k.startswith(("AWS_", "YC_")) for k in env):
        raise Stop("ENV_OVERRIDE")
    if not all(re.fullmatch(r"[a-z0-9-]{1,64}", env[k])
               for k in ("TF_VAR_cloud_id", "TF_VAR_folder_id")):
        raise Stop("INPUT_GATE")
    try:
        if ipaddress.ip_network(env["TF_VAR_admin_cidr"], strict=True).version != 4:
            raise ValueError()
    except ValueError:
        raise Stop("INPUT_GATE") from None


def public_key(text):
    if not isinstance(text, str) or "\n" in text or "\r" in text:
        raise Stop("PUBLIC_KEY")
    parts = text.split()
    if len(parts) < 2 or parts[0] != "ssh-ed25519":
        raise Stop("PUBLIC_KEY")
    try:
        wire = base64.b64decode(parts[1], validate=True)
        expected_prefix = b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20"
        if not wire.startswith(expected_prefix) or len(wire) != len(expected_prefix) + 32:
            raise ValueError()
    except (ValueError, TypeError):
        raise Stop("PUBLIC_KEY") from None
    return " ".join(parts) + "\n"


def provider_key(text):
    try:
        value = json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
        if not isinstance(value, dict) or not all(isinstance(value.get(k), str) and value[k].strip()
                for k in ("id", "service_account_id", "private_key")):
            raise ValueError()
        return value
    except Exception:
        raise Stop("PROVIDER_KEY") from None


def verify_trusted_branch(env):
    request = urllib.request.Request(
        "https://api.github.com/repos/" + REPOSITORY + "/git/ref/heads/diplom-yandexcloud",
        headers={"Authorization": "Bearer " + env["GITHUB_TOKEN"],
                 "Accept": "application/vnd.github+json", "User-Agent": "terraform-plan-only"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            sha = json.load(response)["object"]["sha"]
    except Exception:
        raise Stop("MAIN_METADATA") from None
    if sha != env["TF_PLAN_APPROVED_SHA"]:
        raise Stop("STALE_MAIN")


def command(stage, plan_path):
    # No arbitrary CLI arguments from inputs. Keep this exhaustive allowlist.
    return {
        "version": ["terraform", "version", "-json"],
        "init": ["terraform", "init", "-backend=true", "-input=false", "-lockfile=readonly", "-no-color"],
        "validate": ["terraform", "validate", "-no-color"],
        "plan": ["terraform", "plan", "-input=false", "-refresh=true", "-lock=true",
                 "-lock-timeout=60s", "-no-color", "-detailed-exitcode", "-out=" + str(plan_path)],
        "show": ["terraform", "show", "-json", str(plan_path)],
    }[stage]


def run_stage(stage, root, env, private):
    timeout = {"version": 30, "init": 180, "validate": 120, "plan": 600, "show": 120}[stage]
    with (private / (stage + ".out")).open("wb") as output, (private / (stage + ".err")).open("wb") as error:
        try:
            result = subprocess.run(command(stage, private / "private.tfplan"), cwd=root,
                env=env, stdout=output, stderr=error, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            raise Stop("COMMAND_TIMEOUT", stage=stage) from None
    if result.returncode not in ((0, 2) if stage == "plan" else (0,)):
        raise Stop("COMMAND_FAILED", stage=stage, returncode=result.returncode)
    return result.returncode


def load_private_json(path, stage="show"):
    try:
        if path.stat().st_size > MAX_BYTES:
            raise ValueError()
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
    except Exception:
        raise Stop("PLAN_JSON", stage=stage) from None


def execute(env=None, repository=None):
    env = dict(os.environ if env is None else env)
    gate(env)  # Before network, subprocess, temp credentials or backend work.
    root = (Path(__file__).resolve().parents[2] if repository is None else Path(repository)) / "terraform/infrastructure"
    for name, expected in FINGERPRINTS.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise Stop("SOURCE_OR_BACKEND")
    if (any(root.glob("*.auto.tfvars*")) or any((root / name).exists() for name in
            ("terraform.tfvars", "terraform.tfvars.json", "terraform.tfstate", "terraform.tfstate.backup", ".terraform"))):
        raise Stop("SOURCE_OR_BACKEND")
    # No live key use here until explicit future authorization and activation.
    key = provider_key(env["TF_YC_SERVICE_ACCOUNT_KEY_JSON"])
    pub = public_key(env["TF_SSH_PUBLIC_KEY"])
    verify_trusted_branch(env)
    old_umask = os.umask(0o077)
    try:
        with tempfile.TemporaryDirectory(prefix="terraform-plan-only-") as directory:
            private = Path(directory)
            os.chmod(private, 0o700)
            (private / "provider.json").write_text(json.dumps(key), encoding="utf-8")
            (private / "existing.pub").write_text(pub, encoding="utf-8")
            (private / "terraform.rc").write_text("disable_checkpoint = true\n", encoding="utf-8")
            # Do not pass GitHub token, input JSON or arbitrary ambient env to TF.
            child = {k: env[k] for k in ("PATH", "HOME", "LANG", "LC_ALL") if k in env}
            child.update({"TF_VAR_cloud_id": env["TF_VAR_cloud_id"],
                "TF_VAR_folder_id": env["TF_VAR_folder_id"], "TF_VAR_admin_cidr": env["TF_VAR_admin_cidr"],
                "TF_VAR_ssh_public_key_path": str(private / "existing.pub"),
                "YC_SERVICE_ACCOUNT_KEY_FILE": str(private / "provider.json"),
                "AWS_ACCESS_KEY_ID": env["TF_S3_ACCESS_KEY_ID"],
                "AWS_SECRET_ACCESS_KEY": env["TF_S3_SECRET_ACCESS_KEY"],
                "AWS_EC2_METADATA_DISABLED": "true", "AWS_REGION": "ru-central1",
                "TF_CLI_CONFIG_FILE": str(private / "terraform.rc"),
                "TF_WORKSPACE": "default", "TF_INPUT": "0", "TF_IN_AUTOMATION": "1"})
            run_stage("version", root, child, private)
            if load_private_json(private / "version.out", stage="version").get("terraform_version") != CLI_VERSION:
                raise Stop("CLI_VERSION")
            for stage in ("init", "validate"):
                run_stage(stage, root, child, private)
            plan_exit = run_stage("plan", root, child, private)
            run_stage("show", root, child, private)
            plan = load_private_json(private / "show.out")
            try:
                summary = evaluate(plan)
            except Denied:
                raise Stop("POLICY_DENIED", stage="policy") from None
            if plan_exit != 0:
                raise Stop("NON_NOOP_EXIT")
            verify_trusted_branch(env)
            print(json.dumps({"status": "PLAN_ONLY_VERIFIED_NOOP", "managed_resources": summary["managed_resources"]}, sort_keys=True))
    finally:
        os.umask(old_umask)


def main():
    details = {}
    try:
        execute()
        return 0
    except Stop as error:
        category = str(error) if str(error) in CATEGORIES else "UNEXPECTED_FAILURE"
        if error.stage in {"version", "init", "validate", "plan", "show", "policy"}:
            details["stage"] = error.stage
        if type(error.returncode) is int and -255 <= error.returncode <= 255:
            details["returncode"] = error.returncode
    except (OSError, ValueError, KeyError, TypeError):
        category = "LOCAL_IO_OR_SCHEMA"
    except Exception:
        category = "UNEXPECTED_FAILURE"
    # No exception text, paths, raw subprocess output, plan/IDs/secret values.
    print(json.dumps({"status": "STOP", "category": category, **details}), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
