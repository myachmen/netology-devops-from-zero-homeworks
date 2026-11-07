"""Task184: synthetic reconciliation, actual calls all mocked/offline only."""
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ci/terraform"))
import run_automation as runner
import state_only_policy as policy
from automation_policy import ReviewError
import test_terraform_automation as previous_tests
env = previous_tests.env
from test_terraform_policy import fixture, CANARY


def empty():
    return {"version": "state-only-v1", "drift": [], "outputs": []}


def approved_fixture():
    plan, manifest = fixture(), empty()
    item = copy.deepcopy(plan["resource_changes"][0])
    address = item["address"]
    # Synthetic observed scalar on the existing identity, not a real YC field.
    for section in ("before", "after"):
        plan["resource_changes"][0]["change"][section]["synthetic_observed"] = 2
    for state in (plan["prior_state"]["values"], plan["planned_values"]):
        state["root_module"]["resources"][0]["values"]["synthetic_observed"] = 2
    item["change"].update(actions=["update"])
    item["change"]["before"]["synthetic_observed"] = 1
    item["change"]["after"]["synthetic_observed"] = 2
    plan["resource_drift"] = [item]
    plan["output_changes"] = {"synthetic": {"actions": ["update"], "before": 1,
                                             "after": 2, "after_unknown": False}}
    manifest["drift"] = [{"address": address, "path": ["synthetic_observed"], "before": 1, "after": 2}]
    manifest["outputs"] = [{"name": "synthetic", "path": [], "before": 1, "after": 2}]
    return plan, manifest


class StateOnlyTests(unittest.TestCase):
    def test_positive_exact_synthetic_state_reconciliation(self):
        plan, manifest = approved_fixture()
        decision = policy.approve(plan, manifest)
        self.assertTrue(decision["state_changes"])
        self.assertEqual(decision["policy_version"], "state-only-v1")
        self.assertNotIn(CANARY, json.dumps(decision))

    def test_production_manifest_empty_and_current_counts_not_permission(self):
        manifest = json.loads((ROOT / "ci/terraform/apply-policy.json").read_text())
        self.assertEqual(manifest, empty())
        plan, _ = approved_fixture()
        plan["resource_drift"] *= 9
        summary = policy.review(plan)
        self.assertEqual((summary["actions"], summary["drift_count"], summary["output_change_count"]),
                         ({"no-op": 14}, 9, 1))
        with self.assertRaises(ReviewError): policy.approve(plan, manifest)

    def test_every_resource_write_move_import_is_denied(self):
        for actions in (["create"], ["update"], ["delete"], ["create", "delete"], ["delete", "create"]):
            plan = fixture(); plan["resource_changes"][0]["change"]["actions"] = actions
            with self.assertRaises(ReviewError): policy.approve(plan, empty())
        for where, key, value in (("item", "previous_address", "old"), ("item", "deposed", "old"),
                                  ("change", "importing", {"id": CANARY}), ("change", "generated_config", CANARY),
                                  ("change", "replace_paths", [["id"]])):
            plan = fixture(); item = plan["resource_changes"][0]
            (item if where == "item" else item["change"])[key] = value
            with self.assertRaises(ReviewError): policy.approve(plan, empty())

    def test_unknown_sensitive_markers_in_each_channel(self):
        for kind in ("resource", "drift", "output"):
            for key in ("after_unknown", "before_sensitive", "after_sensitive"):
                plan, manifest = approved_fixture()
                change = (plan["resource_changes"][0]["change"] if kind == "resource" else
                          plan["resource_drift"][0]["change"] if kind == "drift" else plan["output_changes"]["synthetic"])
                change[key] = {"nested": [False, True]}
                with self.assertRaises(ReviewError): policy.approve(plan, manifest)

    def test_exact_paths_values_identity_and_all_rules_required(self):
        for mutation in ("before", "after", "path", "target", "extra", "missing", "unused", "id", "structure"):
            plan, manifest = approved_fixture()
            if mutation in ("before", "after"): manifest["drift"][0][mutation] = 999
            if mutation == "path": manifest["drift"][0]["path"] = ["wrong"]
            if mutation == "target": manifest["drift"][0]["address"] = "not-reviewed"
            if mutation == "extra": plan["resource_drift"][0]["change"]["before"]["private"] = "changed"
            if mutation == "missing": del manifest["drift"]
            if mutation == "unused": manifest["outputs"].append({"name": "unused", "path": [], "before": 1, "after": 2})
            if mutation == "id": manifest["drift"][0]["path"] = ["id"]
            if mutation == "structure": del plan["resource_drift"][0]["change"]["before"]["private"]
            with self.assertRaises(ReviewError): policy.approve(plan, manifest)

    def test_manifests_no_wildcards_duplicates_subtree_or_version(self):
        for mutation in ("wildcard", "duplicate", "subtree", "version", "boolint"):
            plan, manifest = approved_fixture()
            if mutation == "wildcard": manifest["drift"][0]["path"] = ["*"]
            if mutation == "duplicate": manifest["drift"] *= 2
            if mutation == "subtree": manifest["drift"][0]["after"] = {"x": 2}
            if mutation == "version": manifest["version"] = "anything"
            if mutation == "boolint": manifest["drift"][0]["before"] = True
            with self.assertRaises(ReviewError): policy.approve(plan, manifest)

    def test_state_missing_scope_or_noop_value_tampering(self):
        for kind in ("missing", "address", "values"):
            plan = fixture()
            if kind == "missing": del plan["prior_state"]
            if kind == "address": plan["planned_values"]["root_module"]["resources"].pop()
            if kind == "values": plan["resource_changes"][0]["change"]["after"]["private"] = "changed"
            with self.assertRaises(ReviewError): policy.approve(plan, empty())

    def test_binding_checksum_ttl_policy_review_and_source(self):
        manifest = empty()
        with tempfile.TemporaryDirectory() as directory:
            saved = Path(directory) / "private.tfplan"
            saved.write_bytes(b"SYNTHETIC"); saved.chmod(0o600)
            decision = runner.state_policy.approve(fixture())
            binding = {"started": 10, "source_sha": "a" * 40, "binary": runner.saved_checksum(saved),
                       "policy": runner.state_policy.policy_digest(), "review": decision}
            runner.binding_gate(binding, saved, decision, "a" * 40, 910)
            for mutation in ("checksum", "ttl", "backward", "policy", "review", "sha", "mode"):
                b, m, d, now, sha = copy.deepcopy(binding), copy.deepcopy(manifest), copy.deepcopy(decision), 11, "a" * 40
                if mutation == "checksum": b["binary"] = "b" * 64
                if mutation == "ttl": now = 911
                if mutation == "backward": now = 9
                if mutation == "policy": b["policy"] = "b" * 64
                if mutation == "review": d["change_digest"] = "b" * 64
                if mutation == "sha": sha = "b" * 40
                if mutation == "mode": saved.chmod(0o644)
                with self.assertRaises(runner.Stop): runner.binding_gate(b, saved, d, sha, now)
                saved.chmod(0o600)

    def test_gate_events_tags_forks_reruns_no_side_effects(self):
        for key, value in (("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_EVENT_NAME", "pull_request_target"),
                           ("GITHUB_EVENT_NAME", "workflow_dispatch"), ("GITHUB_REF", "refs/tags/v1"),
                           ("GITHUB_REPOSITORY", "fork/repo"), ("GITHUB_RUN_ATTEMPT", "2"),
                           ("TF_APPLY_AUTHORIZATION", "missing")):
            values = env("apply"); values[key] = value
            with patch.object(runner, "verify_checkout") as checkout, patch.object(runner.common, "verify_main") as network:
                with self.assertRaises(runner.Stop): runner.execute(values, "apply")
                checkout.assert_not_called(); network.assert_not_called()

    def test_checkout_dirty_and_active_policy_binding(self):
        with patch.object(runner.subprocess, "check_output", side_effect=["a" * 40, " M script.py"]):
            with self.assertRaisesRegex(runner.Stop, "CHECKOUT_DIRTY"): runner.verify_checkout(ROOT, env())
        self.assertEqual(runner.state_policy.VERSION, "managed-noop-state-refresh-v1")
        self.assertFalse(hasattr(runner, "load_manifest"))

    def test_redacted_error_and_no_native_values(self):
        output = io.StringIO()
        with patch.object(runner, "execute", side_effect=ValueError(CANARY)), redirect_stdout(output):
            self.assertEqual(runner.main(["apply"]), 1)
        self.assertNotIn(CANARY, output.getvalue())


class RuntimeTests(unittest.TestCase):
    simulate = previous_tests.AutomationTests.simulate
    # Reuse meaningful fake native process/S3 adapter and cleanup assertions.
    def test_positive_drift_and_output_same_plan_once(self):
        plan, manifest = approved_fixture()
        error, result, progress, calls, heads = self.simulate("apply", plan, 2)
        self.assertIsNone(error)
        self.assertEqual(calls, ["version", "init", "validate", "plan", "show", "apply"])
        self.assertEqual(heads, 4)
        self.assertEqual(progress["commands"][3]["returncode"], 2)
        self.assertEqual(result["cleanup"], "COMPLETED")

    def test_apply_never_runs_with_uncertain_pre_apply_lock(self):
        plan, manifest = approved_fixture()
        error, _, _, calls, _ = self.simulate("apply", plan, 2, heads=[200, 404, 403, 404])
        self.assertEqual(error, "LOCK_REQUIRES_REVIEW")
        self.assertNotIn("apply", calls)

    def test_apply_failure_timeout_postcheck_uncertainty_no_retry(self):
        plan, manifest = approved_fixture()
        for options, expected in (({"fail": "apply"}, "COMMAND_FAILED"),
                                  ({"timeout": "apply"}, "COMMAND_TIMEOUT"),
                                  ({"heads": [200, 404, 404, 403]}, "LOCK_REQUIRES_REVIEW")):
            error, _, progress, calls, _ = self.simulate("apply", plan, 2, **options)
            self.assertEqual(error, expected)
            self.assertEqual(calls.count("apply"), 1)
            self.assertEqual(calls.count("plan"), 1)
            self.assertEqual(progress["cleanup"], "COMPLETED")

    def test_ttl_expiry_blocks_runtime_apply(self):
        plan, manifest = approved_fixture()
        with patch.object(runner.time, "monotonic", side_effect=[1, 902]):
            error, _, _, calls, _ = self.simulate("apply", plan, 2)
        self.assertEqual(error, "PLAN_TTL")
        self.assertNotIn("apply", calls)


if __name__ == "__main__": unittest.main()
