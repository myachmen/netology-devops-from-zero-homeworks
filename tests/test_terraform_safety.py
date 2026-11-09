"""Offline safety checks. Do not execute future Terraform orchestration."""

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci/terraform"))
SPEC = importlib.util.spec_from_file_location("terraform_runner", ROOT / "ci/terraform/run_infrastructure.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def approved_env():
    return {"TF_CI_ACTIVATION": runner.ACTIVATION, "GITHUB_REPOSITORY": runner.REPOSITORY,
            "GITHUB_EVENT_NAME": "push", "GITHUB_REF": "refs/heads/diplom-yandexcloud", "GITHUB_SHA": "a" * 40,
            **{k: "synthetic-only" for k in ("TF_YC_SERVICE_ACCOUNT_KEY_JSON", "TF_S3_ACCESS_KEY_ID",
               "TF_S3_SECRET_ACCESS_KEY", "TF_VAR_cloud_id", "TF_VAR_folder_id", "TF_VAR_admin_cidr",
               "TF_SSH_PUBLIC_KEY", "GITHUB_TOKEN")}}


class SafetyTests(unittest.TestCase):
    def test_not_a_discoverable_workflow_and_both_jobs_disabled(self):
        template = ROOT / "ci/terraform/terraform-infrastructure.yml.inert"
        self.assertEqual(template.suffix, ".inert")
        text = template.read_text()
        self.assertEqual(text.count("if: ${{ false &&"), 2)
        self.assertIn("TF_CI_ACTIVATION: OWNER_APPROVAL_REQUIRED", text)
        for forbidden in ("workflow_dispatch:", "pull_request_target:", "upload-artifact@", "secrets: inherit"):
            self.assertNotIn(forbidden, text)

    def test_empty_environment_stops_before_process_network_or_credentials(self):
        with patch.dict(runner.os.environ, {}, clear=True), patch.object(runner.subprocess, "run") as process, \
                patch.object(runner.urllib.request, "urlopen") as network, \
                patch.object(runner.tempfile, "TemporaryDirectory") as private:
            stream = io.StringIO()
            with redirect_stderr(stream):
                self.assertEqual(runner.main(), 1)
            process.assert_not_called()
            network.assert_not_called()
            private.assert_not_called()
            self.assertIn("STOP:", stream.getvalue())

    def test_unapproved_event_and_activation_rejected(self):
        for name, value in (("TF_CI_ACTIVATION", "OWNER_APPROVAL_REQUIRED"),
                            ("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_EVENT_NAME", "workflow_dispatch"),
                            ("GITHUB_REF", "refs/heads/feature/diploma-terraform-cicd"),
                            ("GITHUB_REPOSITORY", "untrusted/fork"), ("GITHUB_SHA", "bad")):
            with self.subTest(name=name, value=value):
                env = approved_env()
                env[name] = value
                with self.assertRaises(runner.Stop):
                    runner.guard(env)

    def test_debug_override_and_missing_inputs_rejected(self):
        for name in ("TF_CLI_ARGS", "TF_CLI_ARGS_apply", "TF_LOG", "TF_LOG_PATH", "YC_TOKEN",
                     "TF_DATA_DIR", "TF_CLI_CONFIG_FILE", "TF_REATTACH_PROVIDERS", "AWS_PROFILE"):
            env = approved_env()
            env[name] = "synthetic-only"
            with self.assertRaises(runner.Stop):
                runner.guard(env)
        env = approved_env()
        del env["TF_S3_SECRET_ACCESS_KEY"]
        with self.assertRaises(runner.Stop):
            runner.guard(env)

    def test_approved_guard_is_only_validation(self):
        with patch.object(runner.subprocess, "run") as process, patch.object(runner.urllib.request, "urlopen") as network:
            runner.guard(approved_env())
            process.assert_not_called()
            network.assert_not_called()

    def test_current_trusted_branch_mismatch_stops_without_retry(self):
        with patch.object(runner.urllib.request, "urlopen") as network:
            network.return_value.__enter__.return_value.read.return_value = b'{"object":{"sha":"stale"}}'
            with self.assertRaises(runner.Stop):
                runner.current_trusted_branch(approved_env())
            self.assertEqual(network.call_count, 1)

    def test_exception_details_are_never_printed(self):
        canary = "SYNTHETIC_SECRET_MUST_NEVER_BE_PRINTED"
        stream = io.StringIO()
        with patch.object(runner, "execute", side_effect=RuntimeError(canary)), redirect_stderr(stream):
            self.assertEqual(runner.main(), 1)
        self.assertNotIn(canary, stream.getvalue())


if __name__ == "__main__":
    unittest.main()
