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
import state_only_policy as state_policy
from test_terraform_plan_only import approved_env as old_env
from test_terraform_policy import fixture, CANARY


def env(mode="plan", digest="a" * 64):
    value = old_env()
    value.pop("TF_PLAN_ACTIVATION")
    value.pop("TF_PLAN_APPROVED_SHA")
    value.update(GITHUB_EVENT_NAME="push", TF_AUTOMATION_MODE=mode)
    if mode == "apply":
        value.update(TF_APPLY_AUTHORIZATION=runner.APPLY_AUTHORIZATION)
    return value


def changed():
    value = fixture()
    item = value["resource_changes"][0]
    item["change"]["actions"] = ["update"]
    item["change"]["after"]["private"] = "ANOTHER_SYNTHETIC_SECRET"
    return value


class AutomationTests(unittest.TestCase):
    def simulate(self, mode="plan", plan=None, exitcode=0, fail=None, timeout=None,
                 heads=None, stale=False, bad_json=False, version="1.15.7", mutate_saved=False):
        plan = fixture() if plan is None else plan
        calls, temporary = [], []
        progress = {}
        values = env(mode)
        heads = iter(([200, 404, 404, 404] if mode == "apply" else [200, 404, 404]) if heads is None else heads)
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
            with patch.object(runner, "verify_checkout"), patch.object(runner.common, "verify_trusted_branch", side_effect=api), patch.object(runner.subprocess, "run", side_effect=fake), patch.object(runner, "s3_head", side_effect=lambda *_: next(heads)) as head:
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
        plan = fixture()
        plan["output_changes"] = {"synthetic": {"actions": ["update"], "before": 1, "after": 2,
                                                 "after_unknown": False}}
        manifest = {"version": "state-only-v1", "drift": [], "outputs": [
            {"name": "synthetic", "path": [], "before": 1, "after": 2}]}
        error, result, progress, calls, _ = self.simulate(mode="apply", plan=plan, exitcode=2)
        self.assertIsNone(error)
        self.assertEqual(result["status"], "SAVED_PLAN_APPLY_EXIT_0")
        self.assertEqual(calls.count("plan"), 1)
        self.assertEqual(calls.count("apply"), 1)
        self.assertEqual(progress["commands"][3]["returncode"], 2)

    def test_noop_never_fake_applies(self):
        error, result, _, calls, _ = self.simulate(mode="apply")
        self.assertIsNone(error)
        self.assertEqual(result["status"], "NO_CHANGES_APPLY_SKIPPED")
        self.assertNotIn("apply", calls)

    def test_output_refresh_requires_no_per_field_manifest(self):
        plan = fixture()
        plan["output_changes"]["synthetic"]["after"] = 2
        plan["output_changes"]["synthetic"]["actions"] = ["update"]
        error, _, _, calls, _ = self.simulate(mode="apply", plan=plan, exitcode=2)
        self.assertIsNone(error)
        self.assertEqual(calls.count("apply"), 1)

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
        with patch.object(runner, "verify_checkout") as checkout, patch.object(runner.common, "verify_trusted_branch") as network, patch.object(runner.tempfile, "TemporaryDirectory") as temp:
            with self.assertRaises(runner.Stop): runner.execute({}, "plan")
        checkout.assert_not_called(); network.assert_not_called(); temp.assert_not_called()

    def test_events_refs_reruns_activation_and_overrides(self):
        for key, value in (("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_REF", "refs/heads/feature"), ("GITHUB_RUN_ATTEMPT", "2"), ("GITHUB_REPOSITORY", "fork/repo"), ("TF_AUTOMATION_MODE", "disabled"), ("TF_CLI_ARGS", CANARY), ("AWS_PROFILE", CANARY), ("YC_TOKEN", CANARY)):
            values = env(); values[key] = value
            with self.assertRaises(runner.Stop): runner.gate(values, "plan")
        values = env(); values["GITHUB_EVENT_NAME"] = "workflow_dispatch"
        runner.gate(values, "plan")
        values = env("apply"); values["TF_APPLY_AUTHORIZATION"] = "unapproved"
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

    def check_activation(self, data):
        self.assertEqual(set(data["jobs"]), {"offline", "apply"})
        events = data.get("on", data.get(True))
        self.assertEqual(set(events), {"push", "pull_request"})
        self.assertEqual(events["push"]["branches"], ["diplom-yandexcloud"])
        self.assertNotIn("paths", events["push"])
        self.assertEqual(data["permissions"], {"contents": "read"})
        self.assertFalse(data["concurrency"]["cancel-in-progress"])
        self.assertEqual(data["concurrency"]["group"], "terraform-infrastructure-s3-default")
        job = data["jobs"]["apply"]
        self.assertEqual(job["environment"], "terraform-apply")
        self.assertEqual(job["needs"], "offline")
        for text in ("github.event_name == 'push'", "github.ref == 'refs/heads/diplom-yandexcloud'",
                     "github.repository == 'myachmen/netology-devops-from-zero-homeworks'", "github.run_attempt == 1"):
            self.assertIn(text, job["if"])
        step = job["steps"][-1]
        self.assertEqual(step["env"]["TF_AUTOMATION_MODE"], "apply")
        self.assertEqual(step["env"]["TF_APPLY_AUTHORIZATION"], runner.APPLY_AUTHORIZATION)
        self.assertIn("run_automation.py apply", step["run"])
        self.assertNotIn("secrets.", json.dumps(data["jobs"]["offline"]))
        self.assertNotIn("setup-terraform", json.dumps(data["jobs"]["offline"]))
        self.assertNotIn("run_automation.py", json.dumps(data["jobs"]["offline"]))
        import re
        for action in re.findall(r'uses: ([^\s]+)', (ROOT / "ci/terraform/terraform-automation.yml.inert").read_text()):
            self.assertRegex(action, r'^[^@]+@[a-f0-9]{40}$')

    def test_one_production_job_and_reference_copy(self):
        path = ROOT / "ci/terraform/terraform-automation.yml.inert"
        text = path.read_text()
        self.check_activation(yaml.safe_load(text))
        live = ROOT / ".github/workflows/terraform-automation.yml"
        self.assertTrue(live.is_file())
        active = yaml.safe_load(live.read_text())
        self.assertEqual(set(active["jobs"]), {"offline", "plan"})
        events = active.get("on", active.get(True))
        self.assertEqual(set(events), {"push", "pull_request", "workflow_dispatch"})
        self.assertEqual(active["jobs"]["plan"]["needs"], "offline")
        self.assertEqual(active["jobs"]["plan"]["environment"], "terraform-apply")
        self.assertIn("github.event_name == 'workflow_dispatch'", active["jobs"]["plan"]["if"])
        self.assertEqual(active["jobs"]["plan"]["steps"][-1]["env"]["TF_AUTOMATION_MODE"], "plan")
        self.assertIn("run_automation.py plan", active["jobs"]["plan"]["steps"][-1]["run"])
        self.assertNotIn("run_automation.py apply", live.read_text())
        self.assertNotIn("TF_APPLY_AUTHORIZATION", live.read_text())
        self.assertEqual(yaml.safe_load((ROOT / "ci/terraform/terraform-automation.main-snapshot.yml.inert").read_text())["permissions"], yaml.safe_load(text)["permissions"])
        for forbidden in ("workflow_dispatch:", "pull_request_target:", "upload-artifact@", "cache@", "secrets: inherit"):
            self.assertNotIn(forbidden, text)
        for mutation in ("duplicate", "environment", "secret", "ref"):
            value = yaml.safe_load(text)
            if mutation == "duplicate": value["jobs"]["plan"] = value["jobs"]["apply"]
            if mutation == "environment": value["jobs"]["apply"]["environment"] = "terraform-plan"
            if mutation == "secret": value["jobs"]["offline"]["env"] = {"BAD": "${{ secrets.TF_S3_SECRET_ACCESS_KEY }}"}
            if mutation == "ref": value["jobs"]["apply"]["if"] = "true"
            with self.assertRaises(AssertionError): self.check_activation(value)


if __name__ == "__main__": unittest.main()
