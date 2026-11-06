"""Task179: synthetic plan data; all Terraform, S3 and network activity mocked."""
import copy
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci/terraform"))
sys.path.insert(0, str(ROOT / "tests"))
import run_automation as runner
import automation_policy as policy
from test_terraform_plan_only import approved_env as old_env
from test_terraform_policy import fixture, CANARY


def env(mode="plan", digest="a" * 64):
    value = old_env()
    value.pop("TF_PLAN_ACTIVATION")
    value.pop("TF_PLAN_APPROVED_SHA")
    value.update(GITHUB_EVENT_NAME="push", TF_AUTOMATION_MODE=mode)
    if mode == "apply":
        value.update(TF_APPROVED_APPLY_SHA=value["GITHUB_SHA"], TF_APPROVED_CHANGE_SHA256=digest)
    return value


def changed():
    value = fixture()
    item = value["resource_changes"][0]
    item["change"]["actions"] = ["update"]
    item["change"]["after"]["private"] = "ANOTHER_SYNTHETIC_SECRET"
    return value


class AutomationTests(unittest.TestCase):
    def simulate(self, mode="plan", plan=None, exitcode=0, fail=None, timeout=None,
                 heads=None, approved=None, stale=False, bad_json=False, version="1.15.7", mutate_saved=False):
        plan = fixture() if plan is None else plan
        calls, temporary = [], []
        progress = {}
        values = env(mode, approved or policy.review(plan)["change_digest"])
        heads = iter([200, 404, 404] if heads is None else heads)
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            root = repo / "terraform/infrastructure"
            root.mkdir(parents=True)
            for name in runner.MANIFEST:
                (root / name).write_bytes((ROOT / "terraform/infrastructure" / name).read_bytes())

            def fake(command, **kw):
                stage = command[1]
                self.assertFalse(kw.get("shell", False))
                calls.append(stage)
                child = kw["env"]
                self.assertNotIn("GITHUB_TOKEN", child)
                self.assertNotIn("TF_YC_SERVICE_ACCOUNT_KEY_JSON", child)
                self.assertNotIn("TF_APPROVED_CHANGE_SHA256", child)
                self.assertEqual(child["TF_WORKSPACE"], "default")
                private = Path(child["YC_SERVICE_ACCOUNT_KEY_FILE"]).parent
                temporary.append(private)
                self.assertEqual(private.stat().st_mode & 0o777, 0o700)
                for name in ("provider.json", "existing.pub", "terraform.rc"):
                    self.assertEqual((private / name).stat().st_mode & 0o777, 0o600)
                if stage == timeout:
                    raise runner.subprocess.TimeoutExpired(command, 1, output=CANARY)
                if stage == "version":
                    output = json.dumps({"terraform_version": version})
                elif stage == "show":
                    output = CANARY if bad_json else json.dumps(plan)
                else:
                    output = CANARY
                kw["stdout"].write(output.encode())
                kw["stderr"].write(CANARY.encode())
                if stage == "plan":
                    (private / "private.tfplan").write_bytes(b"SYNTHETIC_PLAN")
                return SimpleNamespace(returncode=1 if stage == fail else exitcode if stage == "plan" else 0)

            def api(_):
                if stale and "show" in calls:
                    raise runner.common.Stop("STALE_MAIN")
                if mutate_saved and "show" in calls:
                    (temporary[-1] / "private.tfplan").write_bytes(b"ALTERED")

            error, result = None, None
            with patch.object(runner, "verify_checkout"), patch.object(runner.common, "verify_main", side_effect=api), patch.object(runner.subprocess, "run", side_effect=fake), patch.object(runner, "s3_head", side_effect=lambda *_: next(heads)) as head:
                try:
                    result = runner.execute(values, mode, repo, progress=progress)
                except Exception as caught:
                    error = str(caught)
            self.assertTrue(all(not p.exists() for p in temporary))
            safe = json.dumps(result or progress)
            self.assertNotIn(CANARY, safe)
            self.assertNotIn("ANOTHER_SYNTHETIC_SECRET", safe)
            return error, result, progress, calls, head.call_count

    def test_noop_plan_five_commands_and_cleanup(self):
        error, result, _, calls, heads = self.simulate()
        self.assertIsNone(error)
        self.assertEqual(result["status"], "PLAN_NOOP")
        self.assertEqual(calls, ["version", "init", "validate", "plan", "show"])
        self.assertEqual(heads, 3)
        self.assertEqual(result["cleanup"], "COMPLETED")

    def test_exit2_show_summary_without_apply(self):
        error, result, _, calls, _ = self.simulate(plan=changed(), exitcode=2)
        self.assertIsNone(error)
        self.assertEqual(result["status"], "PLAN_CHANGES_DETECTED")
        self.assertEqual(result["actions"], {"no-op": 13, "update": 1})
        self.assertNotIn("apply", calls)

    def test_approved_same_run_saved_plan_apply(self):
        error, result, _, calls, _ = self.simulate(mode="apply", plan=changed(), exitcode=2)
        self.assertIsNone(error)
        self.assertEqual(result["status"], "SAVED_PLAN_APPLY_EXIT_0")
        self.assertEqual(calls.count("plan"), 1)
        self.assertEqual(calls[-1], "apply")

    def test_unapproved_digest_never_applies(self):
        error, _, _, calls, _ = self.simulate(mode="apply", plan=changed(), exitcode=2, approved="b" * 64)
        self.assertEqual(error, "CHANGE_APPROVAL")
        self.assertNotIn("apply", calls)

    def test_destruction_replacement_creation_denied(self):
        for actions in (["delete"], ["create"], ["delete", "create"], ["create", "delete"]):
            plan = changed()
            plan["resource_changes"][0]["change"]["actions"] = actions
            summary = policy.review(plan)
            with self.assertRaises(policy.ReviewError):
                policy.allow_apply(plan, summary, summary["change_digest"])

    def test_drift_unknown_and_outputs_deny_apply(self):
        for kind in ("drift", "unknown", "output", "deferred", "check"):
            plan = changed()
            if kind == "drift": plan["resource_drift"] = [{"private": CANARY}]
            if kind == "unknown": plan["resource_changes"][0]["change"]["after_unknown"] = {"private": True}
            if kind == "output": plan["output_changes"]["synthetic"]["actions"] = ["update"]
            if kind == "deferred": plan["deferred_changes"] = [{"private": CANARY}]
            if kind == "check": plan["checks"] = [{"private": CANARY}]
            summary = policy.review(plan)
            with self.assertRaises(policy.ReviewError): policy.allow_apply(plan, summary, summary["change_digest"])

    def test_values_affect_binding_but_not_summary_rows(self):
        first, second = policy.review(fixture()), policy.review(changed())
        self.assertNotEqual(first["change_digest"], second["change_digest"])
        self.assertNotIn(CANARY, json.dumps(second))
        self.assertEqual(set(second["resources"][0]), {"address", "type", "actions"})

    def test_unknown_addresses_schema_and_duplicates_fail_closed(self):
        for kind in ("address", "schema", "duplicate", "version", "incomplete"):
            plan = fixture()
            if kind == "address": plan["resource_changes"][0]["address"] = CANARY
            if kind == "schema": plan["unexpected_action"] = CANARY
            if kind == "duplicate": plan["resource_changes"][1] = plan["resource_changes"][0]
            if kind == "version": plan["terraform_version"] = "unknown"
            if kind == "incomplete": plan["complete"] = False
            with self.assertRaises(policy.ReviewError): policy.review(plan)

    def test_gate_before_any_side_effect(self):
        with patch.object(runner, "verify_checkout") as checkout, patch.object(runner.common, "verify_main") as network, patch.object(runner.tempfile, "TemporaryDirectory") as temp:
            with self.assertRaises(runner.Stop): runner.execute({}, "plan")
        checkout.assert_not_called(); network.assert_not_called(); temp.assert_not_called()

    def test_events_refs_reruns_activation_and_overrides(self):
        for key, value in (("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_REF", "refs/heads/feature"), ("GITHUB_RUN_ATTEMPT", "2"), ("GITHUB_REPOSITORY", "fork/repo"), ("TF_AUTOMATION_MODE", "disabled"), ("TF_CLI_ARGS", CANARY), ("AWS_PROFILE", CANARY), ("YC_TOKEN", CANARY)):
            values = env(); values[key] = value
            with self.assertRaises(runner.Stop): runner.gate(values, "plan")
        values = env("apply"); values["TF_APPROVED_APPLY_SHA"] = "b" * 40
        with self.assertRaises(runner.Stop): runner.gate(values, "apply")

    def test_backend_denial_before_init(self):
        for codes in ([403], [404], [200, 200], [200, 403]):
            error, _, _, calls, _ = self.simulate(heads=codes)
            self.assertEqual(error, "BACKEND_HEAD")
            self.assertEqual(calls, ["version"])

    def test_failed_lock_stops_without_second_plan(self):
        error, _, progress, calls, _ = self.simulate(heads=[200, 404, 200])
        self.assertEqual(error, "LOCK_REQUIRES_REVIEW")
        self.assertEqual(progress["lock"], "PRESENT_OR_UNKNOWN")
        self.assertEqual(calls.count("plan"), 1)

    def test_failures_timeouts_cleanup_and_counts(self):
        for stage in ("init", "validate", "plan", "show"):
            error, _, progress, calls, _ = self.simulate(fail=stage)
            self.assertEqual(error, "COMMAND_FAILED")
            self.assertEqual(calls[-1], stage)
            self.assertEqual(progress["cleanup"], "COMPLETED")
        error, _, progress, calls, _ = self.simulate(timeout="plan")
        self.assertEqual(error, "COMMAND_TIMEOUT")
        self.assertEqual(calls.count("plan"), 1)
        self.assertTrue(progress["commands"][-1]["invoked"])

    def test_bad_json_version_and_stale_main(self):
        self.assertEqual(self.simulate(bad_json=True)[0], "PLAN_JSON")
        self.assertEqual(self.simulate(version="wrong")[3], ["version"])
        error, _, _, calls, _ = self.simulate(mode="apply", stale=True)
        self.assertEqual(error, "STALE_MAIN")
        self.assertNotIn("apply", calls)

    def test_primary_error_retained_if_postcheck_fails(self):
        error, _, progress, _, _ = self.simulate(fail="plan", heads=[200, 404, 403])
        self.assertEqual(error, "COMMAND_FAILED")
        self.assertTrue(progress["postcheck_failed"])

    def test_main_never_prints_exception_text(self):
        output = io.StringIO()
        with patch.object(runner, "execute", side_effect=RuntimeError(CANARY)), redirect_stdout(output):
            self.assertEqual(runner.main(["plan"]), 1)
        self.assertNotIn(CANARY, output.getvalue())

    def test_source_manifest_rejects_missing_template_extras_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in runner.MANIFEST:
                (root / name).write_bytes((ROOT / "terraform/infrastructure" / name).read_bytes())
            runner.source_gate(root)
            (root / "cloud-init.yaml.tftpl").unlink()
            with self.assertRaises(runner.Stop): runner.source_gate(root)
            (root / "cloud-init.yaml.tftpl").symlink_to(ROOT / "terraform/infrastructure/cloud-init.yaml.tftpl")
            with self.assertRaises(runner.Stop): runner.source_gate(root)
            (root / "cloud-init.yaml.tftpl").unlink()
            (root / "cloud-init.yaml.tftpl").write_bytes((ROOT / "terraform/infrastructure/cloud-init.yaml.tftpl").read_bytes())
            (root / "terraform.tfvars").write_text(CANARY)
            with self.assertRaises(runner.Stop): runner.source_gate(root)

    def test_checkout_sha_mismatch(self):
        with patch.object(runner.subprocess, "check_output", return_value="b" * 40):
            with self.assertRaises(runner.Stop): runner.verify_checkout(ROOT, env())

    def test_saved_plan_tampering_blocks_apply(self):
        error, _, _, calls, _ = self.simulate(mode="apply", mutate_saved=True)
        self.assertEqual(error, "PLAN_FILE_CHANGED")
        self.assertNotIn("apply", calls)

    def test_command_allowlist(self):
        for name in ("destroy", "state", "import", "force-unlock", "console", "refresh"):
            with self.assertRaises(KeyError): runner.command(name, Path("private.tfplan"))
        args = runner.command("apply", Path("private.tfplan"))
        self.assertEqual(args[-1], "private.tfplan")
        self.assertNotIn("-auto-approve", args)

    def test_workflow_is_inert_and_main_push_guarded(self):
        text = (ROOT / "ci/terraform/terraform-automation.yml.inert").read_text()
        data = yaml.safe_load(text)
        events = data.get("on", data.get(True))
        self.assertEqual(events["push"]["branches"], ["main"])
        self.assertNotIn("paths", events["push"])
        self.assertEqual(data["permissions"], {"contents": "read"})
        self.assertFalse(data["concurrency"]["cancel-in-progress"])
        self.assertEqual(data["jobs"]["apply"]["environment"], "terraform-production")
        for mode in ("plan", "apply"):
            condition = data["jobs"][mode]["if"]
            self.assertIn("github.event_name == 'push'", condition)
            self.assertIn("TF_AUTOMATION_MODE == '" + mode + "'", condition)
        for forbidden in ("workflow_dispatch:", "pull_request_target:", "upload-artifact@", "secrets: inherit"):
            self.assertNotIn(forbidden, text)
        active = ROOT / ".github/workflows/terraform-automation.yml"
        if active.exists():
            self.check_plan_activation(yaml.safe_load(active.read_text()))

    def check_plan_activation(self, data):
        self.assertEqual(set(data["jobs"]), {"offline", "plan"})
        events = data.get("on", data.get(True))
        self.assertEqual(events["push"]["branches"], ["main"])
        self.assertNotIn("paths", events["push"])
        self.assertNotIn("workflow_dispatch", events)
        self.assertEqual(data["permissions"], {"contents": "read"})
        self.assertFalse(data["concurrency"]["cancel-in-progress"])
        step = data["jobs"]["plan"]["steps"][-1]
        self.assertEqual(step["env"]["TF_AUTOMATION_MODE"], "plan")
        self.assertIn("run_automation.py plan", step["run"])
        self.assertNotIn("run_automation.py apply", json.dumps(data))
        condition = data["jobs"]["plan"]["if"]
        for expected in ("github.event_name == 'push'", "github.ref == 'refs/heads/main'", "github.repository == 'myachmen/netology-devops-from-zero-homeworks'", "github.run_attempt == 1"):
            self.assertIn(expected, condition)
        self.assertNotIn("vars.TF_AUTOMATION_MODE", condition)
        self.assertEqual(data["jobs"]["plan"]["environment"], "terraform-plan")
        self.assertNotIn("terraform-production", json.dumps(data))
        offline = json.dumps(data["jobs"]["offline"])
        self.assertNotIn("secrets.", offline)
        self.assertNotIn("run_automation.py", offline)
        self.assertNotIn("setup-terraform", offline)
        refs = set()
        variables = set()
        import re
        for value in re.findall(r"secrets\.([A-Z0-9_]+)", json.dumps(data)):
            refs.add(value)
        for value in re.findall(r"vars\.([A-Z0-9_]+)", json.dumps(data)):
            variables.add(value)
        self.assertEqual(refs, {"TF_S3_ACCESS_KEY_ID", "TF_S3_SECRET_ACCESS_KEY", "TF_YC_SERVICE_ACCOUNT_KEY_JSON"})
        self.assertEqual(variables, {"TF_ADMIN_CIDR", "TF_CLOUD_ID", "TF_FOLDER_ID", "TF_SSH_PUBLIC_KEY"})

    def test_plan_activation_cannot_expose_apply(self):
        path = ROOT / ".github/workflows/terraform-automation.yml"
        if not path.exists():
            self.skipTest("Activation candidate not present")
        data = yaml.safe_load(path.read_text())
        self.check_plan_activation(data)
        unsafe = copy.deepcopy(data)
        unsafe["jobs"]["apply"] = unsafe["jobs"]["plan"]
        with self.assertRaises(AssertionError): self.check_plan_activation(unsafe)
        unsafe = copy.deepcopy(data)
        unsafe["jobs"]["plan"]["environment"] = "terraform-production"
        with self.assertRaises(AssertionError): self.check_plan_activation(unsafe)
        unsafe = copy.deepcopy(data)
        unsafe["jobs"]["offline"]["env"] = {"BAD": "${{ secrets.TF_S3_SECRET_ACCESS_KEY }}"}
        with self.assertRaises(AssertionError): self.check_plan_activation(unsafe)
        unsafe = copy.deepcopy(data)
        unsafe["jobs"]["plan"]["steps"][-1]["env"]["TF_AUTOMATION_MODE"] = "apply"
        with self.assertRaises(AssertionError): self.check_plan_activation(unsafe)


if __name__ == "__main__": unittest.main()
