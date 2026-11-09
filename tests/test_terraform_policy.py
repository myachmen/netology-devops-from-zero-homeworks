"""Offline synthetic inputs only. Never invoke Terraform or read actual state."""

import copy
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("terraform_plan_policy", ROOT / "ci/terraform/plan_policy.py")
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)
CANARY = "SYNTHETIC_SECRET_MUST_NEVER_BE_PRINTED"


def fixture():
    resources = [
        {"address": address, "mode": "managed", "provider_name": policy.PROVIDER,
         "schema_version": 0, "values": {"id": "synthetic-" + str(i), "private": CANARY}}
        for i, address in enumerate(sorted(policy.EXPECTED_ADDRESSES))
    ]
    return {
        "format_version": "1.2", "terraform_version": policy.TERRAFORM_VERSION,
        "complete": True, "errored": False, "applyable": True,
        "prior_state": {"values": {"root_module": {"resources": copy.deepcopy(resources)}}},
        "planned_values": {"root_module": {"resources": copy.deepcopy(resources)}},
        "resource_changes": [
            {"address": r["address"], "mode": "managed", "provider_name": policy.PROVIDER,
             "change": {"actions": ["no-op"], "before": copy.deepcopy(r["values"]),
                        "after": copy.deepcopy(r["values"]), "after_unknown": {}}}
            for r in resources
        ],
        "output_changes": {"synthetic": {"actions": ["no-op"], "before": CANARY,
                                         "after": CANARY, "after_unknown": False}},
    }


class PolicyTests(unittest.TestCase):
    def cli(self, value=None, raw=None, args=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_text(json.dumps(value) if raw is None else raw)
            output, error = io.StringIO(), io.StringIO()
            with redirect_stdout(output), redirect_stderr(error):
                status = policy.main([str(path)] if args is None else args)
            self.assertNotIn(CANARY, output.getvalue() + error.getvalue())
            self.assertNotIn(str(path), output.getvalue() + error.getvalue())
            return status, output.getvalue(), error.getvalue()

    def assert_denied(self, value):
        status, output, error = self.cli(value)
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertEqual(json.loads(error)["policy"], "DENY")

    def test_expected_noop_and_safe_summary(self):
        status, output, error = self.cli(fixture())
        self.assertEqual(status, 0)
        self.assertEqual(error, "")
        self.assertEqual(json.loads(output), {"policy": "PASS", "mode": "existing-noop-only", "managed_resources": 14})

    def test_actions_deny_by_default(self):
        for actions in (["update"], ["create"], ["delete"], ["create", "delete"],
                        ["delete", "create"], ["read"], ["forget"], [], ["unknown"],
                        ["no-op", "update"], CANARY, None):
            with self.subTest(actions=actions):
                value = fixture()
                value["resource_changes"][0]["change"]["actions"] = actions
                self.assert_denied(value)

    def test_missing_and_empty_state(self):
        for prior in (None, {}, {"values": {}}, {"values": {"root_module": {}}}):
            with self.subTest(prior=prior):
                value = fixture()
                value["prior_state"] = prior
                self.assert_denied(value)

    def test_wrong_state_address_even_with_same_count(self):
        value = fixture()
        value["prior_state"]["values"]["root_module"]["resources"][0]["address"] = CANARY
        self.assert_denied(value)

    def test_missing_state_id(self):
        value = fixture()
        del value["prior_state"]["values"]["root_module"]["resources"][0]["values"]["id"]
        self.assert_denied(value)

    def test_drift_and_deferred_rejected(self):
        for key in ("resource_drift", "deferred_changes"):
            value = fixture()
            value[key] = [{"sensitive": CANARY}]
            self.assert_denied(value)

    def test_schema_version_and_completeness(self):
        for key, field in (("format_version", "999"), ("terraform_version", "1.0.0"),
                           ("complete", False), ("errored", True), ("checks", [CANARY]),
                           ("action_invocations", [CANARY])):
            value = fixture()
            value[key] = field
            self.assert_denied(value)

    def test_missing_required_fields(self):
        for key in ("resource_changes", "planned_values", "complete", "errored"):
            value = fixture()
            del value[key]
            self.assert_denied(value)

    def test_unknown_after_value(self):
        value = fixture()
        value["resource_changes"][0]["change"]["after_unknown"] = {"nested": [{"value": True}]}
        self.assert_denied(value)

    def test_values_must_match_both_states(self):
        for section in ("before", "after"):
            value = fixture()
            value["resource_changes"][0]["change"][section]["private"] = "different-" + CANARY
            self.assert_denied(value)

    def test_changed_planned_state_without_declared_action(self):
        value = fixture()
        value["planned_values"]["root_module"]["resources"][0]["values"]["private"] = "different"
        self.assert_denied(value)

    def test_duplicate_or_missing_changes(self):
        for duplicate in (True, False):
            value = fixture()
            if duplicate:
                value["resource_changes"].append(copy.deepcopy(value["resource_changes"][0]))
            else:
                value["resource_changes"].pop()
            self.assert_denied(value)

    def test_duplicate_state_resources(self):
        value = fixture()
        entries = value["prior_state"]["values"]["root_module"]["resources"]
        entries.append(copy.deepcopy(entries[0]))
        self.assert_denied(value)

    def test_output_changes_and_unknowns(self):
        for key, field in (("actions", ["update"]), ("after", "changed"), ("after_unknown", True)):
            value = fixture()
            value["output_changes"]["synthetic"][key] = field
            self.assert_denied(value)

    def test_import_move_and_provider(self):
        for key, field in (("previous_address", CANARY), ("deposed", CANARY),
                           ("provider_name", CANARY), ("mode", "data")):
            value = fixture()
            value["resource_changes"][0][key] = field
            self.assert_denied(value)
        value = fixture()
        value["resource_changes"][0]["change"]["importing"] = {"id": CANARY}
        self.assert_denied(value)

    def test_malformed_and_duplicate_json_do_not_leak(self):
        for raw in (CANARY, '{"x":"' + CANARY + '","x":2}', '{"x":NaN}', '[]', 'null'):
            status, output, error = self.cli(raw=raw)
            self.assertEqual(status, 1)
            self.assertEqual(output, "")
            self.assertEqual(json.loads(error)["policy"], "DENY")

    def test_io_and_argument_errors_do_not_leak(self):
        for args in ([], [CANARY], [CANARY, CANARY]):
            status, output, error = self.cli(args=args)
            self.assertEqual(status, 1)
            self.assertNotIn(CANARY, output + error)


if __name__ == "__main__":
    unittest.main()
