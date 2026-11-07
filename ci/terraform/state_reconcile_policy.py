"""Active task188 policy: refresh State/outputs, never write managed resources.

No per-field drift manifest. Source approval is the protected single-owner
merge; this pure module validates a fresh private plan, not historic counters.
"""
import hashlib
import json
from automation_policy import ReviewError, require, review
from plan_policy import Denied, EXPECTED_ADDRESSES, PROVIDER, no_unknown, resources

VERSION = "managed-noop-state-refresh-v1"


def policy_digest():
    contract = {"profile": VERSION, "provider": PROVIDER, "terraform": "1.15.7",
                "resources": sorted(EXPECTED_ADDRESSES), "managed_actions": ["no-op"],
                "drift": "known-resource-update-stable-id", "outputs": "known-actions-no-unknown-sensitive"}
    return hashlib.sha256(canonical(contract).encode()).hexdigest()


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError):
        raise ReviewError("PLAN_VALUES") from None


def same(left, right):
    return canonical(left) == canonical(right)


def markers(change):
    require(isinstance(change, dict) and "before" in change and "after" in change, "CHANGE_SCHEMA")
    require(no_unknown(change.get("after_unknown")), "UNKNOWN_VALUE")
    require(no_unknown(change.get("before_sensitive")) and no_unknown(change.get("after_sensitive")), "SENSITIVE_VALUE")
    require(not change.get("importing") and not change.get("generated_config"), "RESOURCE_IMPORT")
    require(not change.get("replace_paths"), "RESOURCE_REPLACE")
    canonical(change)  # Reject non-JSON/NaN fixtures as well as parsed inputs.


def entry(item):
    require(isinstance(item, dict) and item.get("address") in EXPECTED_ADDRESSES, "RESOURCE_SCOPE")
    require(item.get("mode") == "managed" and item.get("provider_name") == PROVIDER, "PROVIDER_SCOPE")
    require("previous_address" not in item and "deposed" not in item, "RESOURCE_MOVE")
    markers(item.get("change"))


def sensitivity(values):
    """Inspect JSON representation wrappers, never dynamic resource value keys."""
    def module(value):
        require(isinstance(value, dict), "STATE_SCHEMA")
        for item in value.get("resources", []):
            require(no_unknown(item.get("sensitive_values")), "SENSITIVE_VALUE")
        for child in value.get("child_modules", []): module(child)
    module(values.get("root_module"))
    outputs = values.get("outputs", {})
    require(isinstance(outputs, dict), "OUTPUT_SCHEMA")
    for output in outputs.values():
        require(isinstance(output, dict) and output.get("sensitive", False) is False, "SENSITIVE_VALUE")


def approve(plan):
    summary = review(plan)  # Exact format/version, complete, known14 actions/scope.
    require(type(plan.get("applyable")) is bool, "PLAN_APPLYABLE_SCHEMA")
    require(not plan.get("checks") and not plan.get("deferred_changes"), "APPLY_UNCERTAINTY")
    try:
        prior_values = plan["prior_state"]["values"]
        planned_values = plan["planned_values"]
        prior = resources(prior_values["root_module"])
        planned = resources(planned_values["root_module"])
    except (Denied, KeyError, TypeError):
        raise ReviewError("STATE_SCHEMA") from None
    require(prior.keys() == planned.keys() == EXPECTED_ADDRESSES, "STATE_SCOPE")
    sensitivity(prior_values); sensitivity(planned_values)
    for item in plan["resource_changes"]:
        entry(item)
        address, change = item["address"], item["change"]
        require(change["actions"] == ["no-op"], "RESOURCE_ACTION")
        require(same(change["before"], change["after"])
                and same(change["after"], prior[address])
                and same(prior[address], planned[address]), "RESOURCE_VALUES")
    seen = set()
    for item in plan.get("resource_drift", []):
        entry(item)
        address, change = item["address"], item["change"]
        require(address not in seen, "DUPLICATE_DRIFT"); seen.add(address)
        require(change.get("actions") == ["update"], "DRIFT_ACTION")
        require(isinstance(change["before"], dict) and isinstance(change["after"], dict), "DRIFT_SCHEMA")
        require(same(change["after"], prior[address]), "DRIFT_AFTER")
        require(change["before"].get("id") == change["after"].get("id") == prior[address]["id"], "DRIFT_IDENTITY")
        # Other observed fields may differ, including containers/status/NAT.
        # Fresh managed actions above MUST still all be no-op.
    for change in plan.get("output_changes", {}).values():
        markers(change)
        actions = change.get("actions")
        require(actions in (["no-op"], ["create"], ["update"], ["delete"]), "OUTPUT_ACTION")
        if actions == ["no-op"]: require(same(change["before"], change["after"]), "OUTPUT_VALUES")
        if actions == ["create"]: require(change["before"] is None, "OUTPUT_VALUES")
        if actions == ["delete"]: require(change["after"] is None, "OUTPUT_VALUES")
    state_changes = bool(seen or summary["output_change_count"])
    require(not state_changes or plan["applyable"], "PLAN_NOT_APPLYABLE")
    return {"policy_version": VERSION, "policy_digest": policy_digest(),
            "change_digest": summary["change_digest"],
            "state_changes": state_changes}
