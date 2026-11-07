#!/usr/bin/env python3
"""Owner-gated main-push automation. Single-owner merge gate; task188 prepares a PR, not live authorization."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import run_plan_only as common
from automation_policy import ReviewError, review
import state_reconcile_policy as state_policy

REPO = common.REPOSITORY
MANIFEST = {".terraform.lock.hcl", "alb.tf", "backend.tf", "cloud-init.yaml.tftpl", "compute.tf", "network.tf", "outputs.tf", "providers.tf", "security.tf", "variables.tf", "versions.tf"}
INPUTS = {"TF_YC_SERVICE_ACCOUNT_KEY_JSON", "TF_S3_ACCESS_KEY_ID", "TF_S3_SECRET_ACCESS_KEY", "TF_VAR_cloud_id", "TF_VAR_folder_id", "TF_VAR_admin_cidr", "TF_SSH_PUBLIC_KEY"}
CONTROL = {"TF_AUTOMATION_MODE", "TF_APPLY_AUTHORIZATION"}
APPLY_AUTHORIZATION = "OWNER_MERGED_STATE_ONLY_V1"
MAX_PLAN_AGE = 900


class Stop(Exception):
    pass


def need(ok, code):
    if not ok:
        raise Stop(code)


def gate(env, mode):
    need(mode in ("plan", "apply") and env.get("TF_AUTOMATION_MODE") == mode, "ACTIVATION")
    need(env.get("GITHUB_REPOSITORY") == REPO and env.get("GITHUB_EVENT_NAME") == "push" and env.get("GITHUB_REF") == "refs/heads/main" and env.get("GITHUB_RUN_ATTEMPT") == "1", "TRUST_GATE")
    need(bool(re.fullmatch("[0-9a-f]{40}", env.get("GITHUB_SHA", ""))), "SHA")
    need(all(isinstance(env.get(k), str) and env[k].strip() for k in INPUTS | {"GITHUB_TOKEN"}), "INPUTS")
    need(not any((k.startswith("TF_") and k not in INPUTS | CONTROL) or k.startswith(("AWS_", "YC_")) for k in env), "ENV_OVERRIDE")
    need(all(re.fullmatch("[a-z0-9-]{1,64}", env[k]) for k in ("TF_VAR_cloud_id", "TF_VAR_folder_id")), "INPUT_FORMAT")
    import ipaddress
    need(ipaddress.ip_network(env["TF_VAR_admin_cidr"], strict=True).version == 4, "INPUT_FORMAT")
    if mode == "apply":
        need(env.get("TF_APPLY_AUTHORIZATION") == APPLY_AUTHORIZATION, "APPLY_AUTHORIZATION")


def saved_checksum(path):
    need(path.is_file() and not path.is_symlink(), "PLAN_FILE")
    need(path.stat().st_mode & 0o777 == 0o600, "PLAN_PERMISSIONS")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binding_gate(binding, saved, policy, source_sha, now):
    need(0 <= now - binding["started"] <= MAX_PLAN_AGE, "PLAN_TTL")
    need(binding["source_sha"] == source_sha, "PLAN_SOURCE")
    need(binding["binary"] == saved_checksum(saved), "PLAN_FILE_CHANGED")
    need(binding["policy"] == state_policy.policy_digest(), "POLICY_CHANGED")
    need(binding["review"] == policy, "POLICY_BINDING")


def source_gate(root):
    need({p.name for p in root.iterdir()} == MANIFEST, "SOURCE_MANIFEST")
    need(all(p.is_file() and not p.is_symlink() for p in root.iterdir()), "SOURCE_ENTRY")
    for name, digest in common.FINGERPRINTS.items():
        need(hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, "BACKEND_OR_LOCK")


def verify_checkout(repo, env):
    value = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], timeout=10, text=True).strip()
    need(value == env["GITHUB_SHA"], "CHECKOUT_SHA")
    dirty = subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"], timeout=10, text=True)
    need(not dirty, "CHECKOUT_DIRTY")


def command(stage, plan):
    if stage == "apply":
        return ["terraform", "apply", "-input=false", "-no-color", "-lock=true", "-lock-timeout=60s", str(plan)]
    return common.command(stage, plan)


def run(stage, root, env, private, calls):
    record = {"stage": stage, "attempted": True, "invoked": False, "returncode": None, "timeout": False}
    calls.append(record)
    timeout = {"version": 30, "init": 180, "validate": 120, "plan": 600, "show": 120, "apply": 900}[stage]
    with (private / (stage + ".out")).open("wb") as out, (private / (stage + ".err")).open("wb") as err:
        try:
            result = subprocess.run(command(stage, private / "private.tfplan"), cwd=root, env=env, stdout=out, stderr=err, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            record["invoked"] = True
            record["timeout"] = True
            raise Stop("COMMAND_TIMEOUT") from None
    record["invoked"] = True
    record["returncode"] = result.returncode
    need(result.returncode in ((0, 2) if stage == "plan" else (0,)), "COMMAND_FAILED")
    return result.returncode


def s3_head(env, key):
    import boto3
    from botocore.config import Config
    from botocore.exceptions import ClientError
    need(key in ("infrastructure/terraform.tfstate", "infrastructure/terraform.tfstate.tflock"), "HEAD_SCOPE")
    client = boto3.client("s3", aws_access_key_id=env["TF_S3_ACCESS_KEY_ID"], aws_secret_access_key=env["TF_S3_SECRET_ACCESS_KEY"], region_name="ru-central1", endpoint_url="https://storage.yandexcloud.net", verify=True, config=Config(connect_timeout=5, read_timeout=15, retries={"total_max_attempts": 1}, s3={"addressing_style": "path"}))
    try:
        return client.head_object(Bucket="netology-diplom-tfstate-myachmen", Key=key)["ResponseMetadata"]["HTTPStatusCode"]
    except ClientError as error:
        return error.response["ResponseMetadata"]["HTTPStatusCode"]
    finally:
        client.close()


def execute(env, mode, repository=None, head=None, progress=None):
    status = {} if progress is None else progress
    status.update({"stage": "trust_gate", "commands": [], "heads": [], "cleanup": "NOT_NEEDED", "lock": "NOT_CHECKED"})
    gate(env, mode)  # Before source, credentials, process, or network use.
    status["stage"] = "source_inputs"
    repo = Path(__file__).resolve().parents[2] if repository is None else Path(repository)
    root = repo / "terraform/infrastructure"
    verify_checkout(repo, env)
    source_gate(root)
    policy_digest = state_policy.policy_digest() if mode == "apply" else None
    key = common.provider_key(env["TF_YC_SERVICE_ACCOUNT_KEY_JSON"])
    pub = common.public_key(env["TF_SSH_PUBLIC_KEY"])
    trusted = dict(env, TF_PLAN_APPROVED_SHA=env["GITHUB_SHA"])
    common.verify_main(trusted)
    head = s3_head if head is None else head
    status.update({"mode": mode, "source_sha": env["GITHUB_SHA"]})
    old = os.umask(0o077)
    try:
        with tempfile.TemporaryDirectory(prefix="terraform-automation-") as directory:
            private = Path(directory)
            status["cleanup"] = "PENDING"
            os.chmod(private, 0o700)
            (private / "provider.json").write_text(json.dumps(key))
            (private / "existing.pub").write_text(pub)
            (private / "terraform.rc").write_text("disable_checkpoint = true\n")
            child = {k: env[k] for k in ("PATH", "HOME", "LANG", "LC_ALL") if k in env}
            child.update({"AWS_ACCESS_KEY_ID": env["TF_S3_ACCESS_KEY_ID"], "AWS_SECRET_ACCESS_KEY": env["TF_S3_SECRET_ACCESS_KEY"], "AWS_REGION": "ru-central1", "AWS_EC2_METADATA_DISABLED": "true", "YC_SERVICE_ACCOUNT_KEY_FILE": str(private / "provider.json"), "TF_CLI_CONFIG_FILE": str(private / "terraform.rc"), "TF_DATA_DIR": str(private / "data"), "TF_WORKSPACE": "default", "TF_INPUT": "0", "TF_IN_AUTOMATION": "1", "TF_VAR_ssh_public_key_path": str(private / "existing.pub"), **{k: env[k] for k in ("TF_VAR_cloud_id", "TF_VAR_folder_id", "TF_VAR_admin_cidr")}})
            status["stage"] = "version"
            run("version", root, child, private, status["commands"])
            need(common.load_private_json(private / "version.out").get("terraform_version") == "1.15.7", "CLI_VERSION")
            for label, path, expected in (("state", "infrastructure/terraform.tfstate", 200), ("pre_lock", "infrastructure/terraform.tfstate.tflock", 404)):
                status["stage"] = label
                code = head(env, path)
                status["heads"].append({"target": label, "http": code})
                need(code == expected, "BACKEND_HEAD")
            touched_backend = False
            try:
                for stage in ("init", "validate"):
                    status["stage"] = stage
                    touched_backend = True
                    run(stage, root, child, private, status["commands"])
                status["stage"] = "plan"
                plan_started = time.monotonic()
                exitcode = run("plan", root, child, private, status["commands"])
                saved = private / "private.tfplan"
                binary_digest = saved_checksum(saved)
                status["stage"] = "show"
                run("show", root, child, private, status["commands"])
                plan = common.load_private_json(private / "show.out")
                summary = review(plan)
                need(exitcode != 0 or (all(x["actions"] == ["no-op"] for x in summary["resources"]) and not summary["output_change_count"]), "EXIT_JSON_MISMATCH")
                status.update(summary)
                status["status"] = "PLAN_NOOP" if exitcode == 0 else "PLAN_CHANGES_DETECTED"
                if mode == "apply":
                    status["stage"] = "apply_gate"
                    approved = state_policy.approve(plan)
                    need(approved["policy_digest"] == policy_digest, "POLICY_CHANGED")
                    status.update({k: approved[k] for k in ("policy_version", "policy_digest", "state_changes")})
                    binding = {"started": plan_started, "binary": binary_digest,
                               "policy": policy_digest, "source_sha": env["GITHUB_SHA"],
                               "review": approved}
                    # Check absent lock before any apply, not only after it.
                    code = head(env, "infrastructure/terraform.tfstate.tflock")
                    status["heads"].append({"target": "pre_apply_lock", "http": code})
                    need(code == 404, "LOCK_REQUIRES_REVIEW")
                    common.verify_main(trusted)
                    verify_checkout(repo, env)
                    source_gate(root)
                    current_plan = common.load_private_json(private / "show.out")
                    current_review = state_policy.approve(current_plan)
                    binding_gate(binding, saved, current_review,
                                 env["GITHUB_SHA"], time.monotonic())
                    if not approved["state_changes"]:
                        need(exitcode == 0, "EXIT_JSON_MISMATCH")
                        status["status"] = "NO_CHANGES_APPLY_SKIPPED"
                    else:
                        status["stage"] = "apply"
                        run("apply", root, child, private, status["commands"])
                        status["status"] = "SAVED_PLAN_APPLY_EXIT_0"
                common.verify_main(trusted)
            finally:
                if touched_backend:
                    # Preserve primary failing stage even if postcheck also fails.
                    primary = sys.exc_info()[0] is not None
                    try:
                        code = head(env, "infrastructure/terraform.tfstate.tflock")
                        status["heads"].append({"target": "post_lock", "http": code})
                        status["lock"] = "ABSENT_404" if code == 404 else "PRESENT_OR_UNKNOWN"
                        need(code == 404, "LOCK_REQUIRES_REVIEW")
                    except Exception:
                        status["lock"] = "PRESENT_OR_UNKNOWN"
                        status["postcheck_failed"] = True
                        if not primary:
                            raise Stop("LOCK_REQUIRES_REVIEW") from None
        status["cleanup"] = "COMPLETED"
        return status
    finally:
        os.umask(old)
        if "private" in locals():
            status["cleanup"] = "COMPLETED" if not private.exists() else "FAILED"


def main(argv=None):
    progress = {}
    try:
        args = sys.argv[1:] if argv is None else argv
        need(len(args) == 1, "MODE")
        result = execute(dict(os.environ), args[0], progress=progress)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as error:
        safe = str(error) if isinstance(error, (Stop, ReviewError, common.Stop)) and re.fullmatch("[A-Z_]{1,60}", str(error)) else "LOCAL_NETWORK_OR_SCHEMA"
        kind = type(error).__name__ if type(error).__name__ in {"Stop", "ReviewError", "ValueError", "JSONDecodeError", "FileNotFoundError", "PermissionError"} else "OtherException"
        print(json.dumps({**progress, "status": "STOP", "category": safe, "exception_class": kind}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
