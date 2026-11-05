"""Synthetic offline tests. All process and network calls are mocked."""

import ast
import base64
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci/terraform"))
SPEC = importlib.util.spec_from_file_location("plan_only_runner", ROOT / "ci/terraform/run_plan_only.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)
FIXTURE_SPEC = importlib.util.spec_from_file_location("plan_only_fixture", ROOT / "tests/test_terraform_policy.py")
fixtures = importlib.util.module_from_spec(FIXTURE_SPEC)
FIXTURE_SPEC.loader.exec_module(fixtures)
CANARY = "SYNTHETIC_SECRET_MUST_NEVER_BE_PRINTED"


def approved_env():
    wire = b"\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20" + b"x" * 32
    return {"TF_PLAN_ACTIVATION": runner.APPROVAL_MARKER, "TF_PLAN_APPROVED_SHA": "a" * 40,
        "GITHUB_SHA": "a" * 40, "GITHUB_REPOSITORY": runner.REPOSITORY,
        "GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main",
        "GITHUB_RUN_ATTEMPT": "1", "GITHUB_TOKEN": CANARY,
        "TF_YC_SERVICE_ACCOUNT_KEY_JSON": json.dumps({"id": "synthetic-id",
            "service_account_id": "synthetic-sa", "private_key": CANARY}),
        "TF_S3_ACCESS_KEY_ID": CANARY, "TF_S3_SECRET_ACCESS_KEY": CANARY,
        "TF_VAR_cloud_id": "synthetic-cloud", "TF_VAR_folder_id": "synthetic-folder",
        "TF_VAR_admin_cidr": "192.0.2.1/32",
        "TF_SSH_PUBLIC_KEY": "ssh-ed25519 " + base64.b64encode(wire).decode(),
        "PATH": "/usr/bin", "HOME": "/synthetic-home"}


class PlanOnlyTests(unittest.TestCase):
    def simulate(self, fail=None, timeout=None, plan=None, plan_exit=0, bad_json=False,
                 version="1.15.7", stale_after=False, extra_file=None):
        calls, directories = [], []
        result_plan = fixtures.fixture() if plan is None else plan
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            root = repo / "terraform/infrastructure"
            root.mkdir(parents=True)
            for name in runner.FINGERPRINTS:
                (root / name).write_bytes((ROOT / "terraform/infrastructure" / name).read_bytes())
            if extra_file:
                (root / extra_file).write_text(CANARY)

            def fake_process(command, **kwargs):
                self.assertEqual(command[0], "terraform")
                stage = command[1]
                self.assertIn(stage, {"version", "init", "validate", "plan", "show"})
                self.assertFalse(kwargs.get("shell", False))
                self.assertIs(kwargs["check"], False)
                calls.append(command)
                child = kwargs["env"]
                self.assertNotIn("GITHUB_TOKEN", child)
                self.assertNotIn("TF_YC_SERVICE_ACCOUNT_KEY_JSON", child)
                self.assertEqual(child["TF_WORKSPACE"], "default")
                self.assertEqual(child["AWS_EC2_METADATA_DISABLED"], "true")
                self.assertEqual(child["TF_VAR_cloud_id"], "synthetic-cloud")
                private = Path(child["YC_SERVICE_ACCOUNT_KEY_FILE"]).parent
                directories.append(private)
                self.assertEqual(private.stat().st_mode & 0o777, 0o700)
                for name in ("provider.json", "existing.pub", "terraform.rc"):
                    self.assertEqual((private / name).stat().st_mode & 0o777, 0o600)
                self.assertIn(CANARY, (private / "provider.json").read_text())
                if stage == timeout:
                    raise runner.subprocess.TimeoutExpired(command, 1, output=CANARY)
                if stage == "version":
                    output = json.dumps({"terraform_version": version})
                elif stage == "show":
                    output = CANARY if bad_json else json.dumps(result_plan)
                else:
                    output = CANARY
                kwargs["stdout"].write(output.encode())
                kwargs["stderr"].write(CANARY.encode())
                if stage == "plan":
                    (private / "private.tfplan").write_bytes(b"synthetic-only")
                code = 1 if stage == fail else (plan_exit if stage == "plan" else 0)
                return SimpleNamespace(returncode=code)

            def fake_api(*_args, **_kwargs):
                self.assertEqual(_kwargs["timeout"], 20)
                sha = "b" * 40 if stale_after and len(calls) == 5 else "a" * 40
                return io.BytesIO(json.dumps({"object": {"sha": sha}}).encode())

            output, error = io.StringIO(), io.StringIO()
            with patch.object(runner.subprocess, "run", side_effect=fake_process), \
                    patch.object(runner.urllib.request, "urlopen", side_effect=fake_api) as network, \
                    redirect_stdout(output), redirect_stderr(error):
                caught = None
                try:
                    runner.execute(approved_env(), repo)
                except runner.Stop as exc:
                    caught = str(exc)
                network_count = network.call_count
            self.assertNotIn(CANARY, output.getvalue() + error.getvalue())
            self.assertTrue(all(not p.exists() for p in directories))
            return caught, calls, output.getvalue(), network_count

    def test_complete_noop_path_is_five_commands_without_write_action(self):
        error, calls, output, count = self.simulate()
        self.assertIsNone(error)
        self.assertEqual([c[1] for c in calls], ["version", "init", "validate", "plan", "show"])
        self.assertEqual(count, 2)
        self.assertEqual(json.loads(output), {"status": "PLAN_ONLY_VERIFIED_NOOP", "managed_resources": 14})

    def test_command_allowlist_no_apply_destroy_import_state_or_unlock(self):
        for verb in ("apply", "destroy", "import", "state", "force-unlock", "refresh", "test", "console"):
            with self.subTest(verb=verb), self.assertRaises(KeyError):
                runner.command(verb, Path("synthetic.tfplan"))
        tree = ast.parse((ROOT / "ci/terraform/run_plan_only.py").read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        self.assertNotIn("run_infrastructure", imports)
        process_calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                         and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
                         and n.func.value.id == "subprocess"]
        self.assertEqual(len(process_calls), 1)
        self.assertEqual(process_calls[0].func.attr, "run")

    def test_locked_refresh_plan_and_readonly_provider_lock(self):
        plan = runner.command("plan", Path("synthetic.tfplan"))
        for flag in ("-lock=true", "-lock-timeout=60s", "-refresh=true", "-input=false"):
            self.assertIn(flag, plan)
        init = runner.command("init", Path("synthetic.tfplan"))
        self.assertIn("-lockfile=readonly", init)
        self.assertIn("-backend=true", init)
        for forbidden in ("-lock=false", "-upgrade", "-migrate-state", "-reconfigure", "-force-copy"):
            self.assertNotIn(forbidden, plan + init)

    def test_gate_before_network_process_and_credentials(self):
        with patch.object(runner.subprocess, "run") as process, \
                patch.object(runner.urllib.request, "urlopen") as network, \
                patch.object(runner.tempfile, "TemporaryDirectory") as private:
            with self.assertRaises(runner.Stop):
                runner.execute({}, Path("/synthetic-nonexistent"))
            process.assert_not_called()
            network.assert_not_called()
            private.assert_not_called()

    def test_events_main_sha_approval_and_rerun_gates(self):
        for name, value in (("TF_PLAN_ACTIVATION", "OWNER_APPROVAL_REQUIRED"),
                ("GITHUB_EVENT_NAME", "push"), ("GITHUB_EVENT_NAME", "pull_request"),
                ("GITHUB_EVENT_NAME", "pull_request_target"), ("GITHUB_REPOSITORY", "untrusted/fork"),
                ("GITHUB_REF", "refs/heads/feature/example"), ("GITHUB_REF", "refs/tags/v1"),
                ("TF_PLAN_APPROVED_SHA", "b" * 40), ("GITHUB_SHA", "bad"), ("GITHUB_RUN_ATTEMPT", "2")):
            with self.subTest(name=name, value=value):
                env = approved_env()
                env[name] = value
                with self.assertRaises(runner.Stop):
                    runner.gate(env)

    def test_every_required_input_and_token(self):
        for name in runner.REQUIRED | {"GITHUB_TOKEN"}:
            env = approved_env()
            env.pop(name)
            with self.subTest(name=name), self.assertRaises(runner.Stop):
                runner.gate(env)

    def test_unexpected_env_overrides(self):
        for name in ("TF_CLI_ARGS", "TF_CLI_ARGS_plan", "TF_LOG", "TF_LOG_PATH", "TF_WORKSPACE",
                "TF_CLI_CONFIG_FILE", "TF_DATA_DIR", "TF_VAR_unapproved", "TF_REATTACH_PROVIDERS",
                "YC_TOKEN", "YC_ENDPOINT", "YC_SERVICE_ACCOUNT_KEY_FILE", "AWS_PROFILE",
                "AWS_ACCESS_KEY_ID", "AWS_ENDPOINT_URL"):
            env = approved_env()
            env[name] = CANARY
            with self.subTest(name=name), self.assertRaises(runner.Stop):
                runner.gate(env)

    def test_input_shapes_and_public_key_schema(self):
        for name, value in (("TF_VAR_cloud_id", "bad value"), ("TF_VAR_admin_cidr", "invalid"),
                            ("TF_VAR_admin_cidr", "2001:db8::/64")):
            env = approved_env()
            env[name] = value
            with self.assertRaises(runner.Stop):
                runner.gate(env)
        for key in (CANARY, "ssh-ed25519 invalid", "ssh-rsa aaaa", approved_env()["TF_SSH_PUBLIC_KEY"] + "\n"):
            with self.assertRaises(runner.Stop):
                runner.public_key(key)

    def test_provider_schema_errors_do_not_escape(self):
        for text in (CANARY, "{}", '[]', '{"id":NaN}', '{"id":"a","id":"b"}'):
            with self.assertRaises(runner.Stop) as error:
                runner.provider_key(text)
            self.assertEqual(str(error.exception), "PROVIDER_KEY")

    def test_command_failure_stops_without_show_or_retry(self):
        error, calls, output, _ = self.simulate(fail="plan")
        self.assertEqual(error, "COMMAND_FAILED")
        self.assertEqual([c[1] for c in calls], ["version", "init", "validate", "plan"])
        self.assertEqual(output, "")

    def test_init_failure_stops_before_planning(self):
        error, calls, output, _ = self.simulate(fail="init")
        self.assertEqual(error, "COMMAND_FAILED")
        self.assertEqual(len(calls), 2)
        self.assertEqual(output, "")

    def test_timeout_stops_and_cleans_private_files(self):
        error, calls, output, _ = self.simulate(timeout="plan")
        self.assertEqual(error, "COMMAND_TIMEOUT")
        self.assertEqual(len(calls), 4)
        self.assertEqual(output, "")

    def test_exit2_and_noop_json_do_not_claim_success(self):
        error, calls, output, _ = self.simulate(plan_exit=2)
        self.assertEqual(error, "NON_NOOP_EXIT")
        self.assertEqual(len(calls), 5)
        self.assertEqual(output, "")

    def test_policy_drift_change_and_schema_stop(self):
        for kind in ("update", "drift", "schema"):
            plan = fixtures.fixture()
            if kind == "update":
                plan["resource_changes"][0]["change"]["actions"] = ["update"]
            elif kind == "drift":
                plan["resource_drift"] = [{"synthetic": CANARY}]
            else:
                plan["format_version"] = "unknown"
            error, calls, output, _ = self.simulate(plan=plan)
            self.assertEqual(error, "POLICY_DENIED")
            self.assertEqual(len(calls), 5)
            self.assertEqual(output, "")

    def test_malformed_json_stops_without_leak(self):
        error, _, output, _ = self.simulate(bad_json=True)
        self.assertEqual(error, "PLAN_JSON")
        self.assertEqual(output, "")

    def test_wrong_cli_version_stops_before_init(self):
        error, calls, output, _ = self.simulate(version="unknown")
        self.assertEqual(error, "CLI_VERSION")
        self.assertEqual(len(calls), 1)
        self.assertEqual(output, "")

    def test_stale_main_after_plan_is_not_success(self):
        error, calls, output, count = self.simulate(stale_after=True)
        self.assertEqual(error, "STALE_MAIN")
        self.assertEqual(len(calls), 5)
        self.assertEqual(count, 2)
        self.assertEqual(output, "")

    def test_unreviewed_variable_or_state_file_before_network(self):
        for name in ("terraform.tfvars", "unexpected.auto.tfvars.json", "terraform.tfstate", ".terraform"):
            error, calls, output, count = self.simulate(extra_file=name)
            self.assertEqual(error, "SOURCE_OR_BACKEND")
            self.assertEqual(calls, [])
            self.assertEqual(count, 0)
            self.assertEqual(output, "")

    def test_network_error_is_fixed_category_without_retry(self):
        with patch.object(runner.urllib.request, "urlopen", side_effect=RuntimeError(CANARY)) as network:
            with self.assertRaises(runner.Stop) as error:
                runner.verify_main(approved_env())
            self.assertEqual(str(error.exception), "MAIN_METADATA")
            self.assertEqual(network.call_count, 1)

    def test_main_error_category_does_not_print_exception_text(self):
        for error in (RuntimeError(CANARY), runner.Stop(CANARY, stage=CANARY), ValueError(CANARY),
                      runner.Stop("COMMAND_TIMEOUT", stage="plan"),
                      runner.Stop("COMMAND_FAILED", stage="init", returncode=1)):
            output, stderr = io.StringIO(), io.StringIO()
            with patch.object(runner, "execute", side_effect=error), redirect_stdout(output), redirect_stderr(stderr):
                self.assertEqual(runner.main(), 1)
            self.assertEqual(output.getvalue(), "")
            self.assertNotIn(CANARY, stderr.getvalue())
            self.assertEqual(json.loads(stderr.getvalue())["status"], "STOP")
            if isinstance(error, runner.Stop) and error.stage == "init":
                self.assertEqual(json.loads(stderr.getvalue()), {"status": "STOP", "category": "COMMAND_FAILED",
                                 "stage": "init", "returncode": 1})

    def test_template_is_non_discoverable_disabled_and_manual_only(self):
        path = ROOT / "ci/terraform/terraform-plan-only.yml.inert"
        self.assertEqual(path.suffix, ".inert")
        text = path.read_text()
        self.assertEqual(text.count("if: ${{ false &&"), 1)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("TF_PLAN_ACTIVATION: OWNER_APPROVAL_REQUIRED", text)
        self.assertIn("contents: read", text)
        self.assertIn("cancel-in-progress: false", text)
        for forbidden in ("pull_request:", "pull_request_target:", "push:", "release:", "upload-artifact@", "run_infrastructure.py"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
