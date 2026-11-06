"""Sanitized change review; no network, Terraform, or approval at import time."""
import hashlib
import json
from collections import Counter
from plan_policy import EXPECTED_ADDRESSES, PROVIDER, no_unknown


class ReviewError(Exception):
    pass


def require(ok, category):
    if not ok:
        raise ReviewError(category)


def review(plan):
    require(isinstance(plan, dict), "PLAN_SCHEMA")
    allowed = {"format_version", "terraform_version", "variables", "planned_values", "resource_changes", "resource_drift", "output_changes", "prior_state", "configuration", "relevant_attributes", "checks", "timestamp", "applyable", "complete", "errored", "deferred_changes"}
    require(not (plan.keys() - allowed), "UNKNOWN_PLAN_FIELD")
    require(plan.get("format_version") == "1.2" and plan.get("terraform_version") == "1.15.7", "PLAN_VERSION")
    require(plan.get("complete") is True and plan.get("errored") is False, "PLAN_INCOMPLETE")
    changes = plan.get("resource_changes")
    require(isinstance(changes, list), "PLAN_SCHEMA")
    seen, rows, counts = set(), [], Counter()
    for item in changes:
        require(isinstance(item, dict), "PLAN_SCHEMA")
        address = item.get("address")
        require(address in EXPECTED_ADDRESSES and address not in seen, "UNREVIEWED_RESOURCE")
        require(item.get("mode") == "managed" and item.get("provider_name") == PROVIDER, "PROVIDER_SCOPE")
        seen.add(address)
        change = item.get("change")
        require(isinstance(change, dict), "PLAN_SCHEMA")
        actions = change.get("actions")
        require(actions in (["no-op"], ["create"], ["update"], ["delete"], ["delete", "create"], ["create", "delete"]), "ACTION_SCHEMA")
        label = "+".join(actions)
        counts[label] += 1
        rows.append({"address": address, "type": address.split(".", 1)[0], "actions": actions})
    require(seen == EXPECTED_ADDRESSES, "RESOURCE_COUNT")
    drift = plan.get("resource_drift", [])
    require(isinstance(drift, list), "DRIFT_SCHEMA")
    # Aggregate binding, never per-secret hashes or raw values. Ordering stable.
    binding = {"resources": sorted(changes, key=lambda x: x["address"]),
               "drift": drift, "outputs": plan.get("output_changes", {}),
               "deferred": plan.get("deferred_changes", []), "checks": plan.get("checks", [])}
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    outputs = plan.get("output_changes", {})
    require(isinstance(outputs, dict) and all(isinstance(v, dict) for v in outputs.values()), "OUTPUT_SCHEMA")
    return {"managed_resources": len(seen), "actions": dict(sorted(counts.items())),
            "resources": sorted(rows, key=lambda x: x["address"]),
            "output_change_count": sum(v.get("actions") != ["no-op"] for v in outputs.values()),
            "drift_count": len(drift), "change_digest": digest}


def allow_apply(plan, summary, approved_digest):
    require(isinstance(approved_digest, str) and len(approved_digest) == 64 and approved_digest == summary["change_digest"], "CHANGE_APPROVAL")
    require(not plan.get("resource_drift") and not plan.get("deferred_changes") and not plan.get("checks"), "APPLY_UNCERTAINTY")
    for item in plan["resource_changes"]:
        change = item["change"]
        require(change["actions"] in (["no-op"], ["update"]), "DESTRUCTIVE_ACTION")
        require(not item.get("previous_address") and not item.get("deposed") and not change.get("importing") and not change.get("generated_config"), "RESOURCE_MOVE")
        require(no_unknown(change.get("after_unknown")), "UNKNOWN_VALUE")
    outputs = plan.get("output_changes", {})
    require(isinstance(outputs, dict), "OUTPUT_SCHEMA")
    for output in outputs.values():
        require(isinstance(output, dict) and output.get("actions") == ["no-op"] and no_unknown(output.get("after_unknown")), "OUTPUT_CHANGE")
