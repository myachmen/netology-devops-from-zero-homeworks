#!/usr/bin/env python3
"""Offline, fail-closed policy for the first existing-infrastructure no-op.

Input: private `terraform show -json` file. Output: fixed categories only.
This is an additional client-side guard, not an IAM or code-review boundary.
No Terraform process, network request, state write, or import-time action.
"""

import json
import sys
from pathlib import Path

TERRAFORM_VERSION = "1.15.7"
PROVIDER = "registry.terraform.io/yandex-cloud/yandex"
EXPECTED_ADDRESSES = frozenset(
    {
        'yandex_compute_instance.k8s["k8s-control-1"]',
        'yandex_compute_instance.k8s["k8s-worker-1"]',
        'yandex_compute_instance.k8s["k8s-worker-2"]',
        "yandex_vpc_network.diplom",
        "yandex_vpc_subnet.subnet_a",
        "yandex_vpc_subnet.subnet_d",
        "yandex_vpc_subnet.subnet_e",
        "yandex_vpc_security_group.k8s",
        "yandex_vpc_security_group.alb",
        "yandex_alb_target_group.k8s_workers",
        "yandex_alb_backend_group.k8s_ingress",
        "yandex_alb_http_router.diplom",
        "yandex_alb_virtual_host.diplom",
        "yandex_alb_load_balancer.diplom",
    }
)
MAX_BYTES = 20 * 1024 * 1024


class Denied(Exception):
    """Contains only an internal, non-sensitive reason code."""


def require(condition, code):
    if not condition:
        raise Denied(code)


def no_unknown(value):
    """Accept only false leaves, empty collections or absence, never unknowns."""
    if value is False or value is None:
        return True
    if isinstance(value, dict):
        return all(no_unknown(v) for v in value.values())
    if isinstance(value, list):
        return all(no_unknown(v) for v in value)
    return False


def resources(module):
    require(isinstance(module, dict), "STATE_SCHEMA")
    result = {}
    entries = module.get("resources", [])
    children = module.get("child_modules", [])
    require(isinstance(entries, list) and isinstance(children, list), "STATE_SCHEMA")
    for resource in entries:
        require(isinstance(resource, dict), "STATE_SCHEMA")
        address = resource.get("address")
        require(isinstance(address, str) and address in EXPECTED_ADDRESSES, "STATE_SCOPE")
        require(address not in result, "DUPLICATE_RESOURCE")
        require(resource.get("mode") == "managed", "RESOURCE_MODE")
        require(resource.get("provider_name") == PROVIDER, "PROVIDER")
        values = resource.get("values")
        require(isinstance(values, dict), "STATE_SCHEMA")
        require(isinstance(values.get("id"), str) and bool(values["id"]), "STATE_ID")
        result[address] = values
    for child in children:
        nested = resources(child)
        require(not (result.keys() & nested.keys()), "DUPLICATE_RESOURCE")
        result.update(nested)
    return result


def evaluate(plan):
    require(isinstance(plan, dict), "PLAN_SCHEMA")
    allowed_fields = {"format_version", "terraform_version", "variables", "planned_values",
                      "resource_changes", "resource_drift", "output_changes", "prior_state",
                      "configuration", "relevant_attributes", "checks", "timestamp",
                      "applyable", "complete", "errored", "deferred_changes"}
    require(not (plan.keys() - allowed_fields), "UNKNOWN_PLAN_FIELD")
    require(plan.get("format_version") == "1.2", "FORMAT_VERSION")
    require(plan.get("terraform_version") == TERRAFORM_VERSION, "TERRAFORM_VERSION")
    require(plan.get("complete") is True and plan.get("errored") is False, "INCOMPLETE_PLAN")
    require(plan.get("resource_drift", []) == [], "DRIFT")
    require(plan.get("deferred_changes", []) == [], "DEFERRED")
    # This baseline has no check blocks. A new check schema needs explicit review.
    require(plan.get("checks", []) == [], "CHECKS_REQUIRE_REVIEW")
    prior = plan.get("prior_state")
    require(isinstance(prior, dict) and isinstance(prior.get("values"), dict), "MISSING_STATE")
    planned = plan.get("planned_values")
    require(isinstance(planned, dict), "MISSING_PLANNED_VALUES")
    old = resources(prior["values"].get("root_module"))
    new = resources(planned.get("root_module"))
    require(old.keys() == EXPECTED_ADDRESSES, "STATE_SCOPE")
    require(new.keys() == EXPECTED_ADDRESSES, "PLANNED_SCOPE")
    changes = plan.get("resource_changes")
    require(isinstance(changes, list), "CHANGE_SCHEMA")
    seen = set()
    for item in changes:
        require(isinstance(item, dict), "CHANGE_SCHEMA")
        address = item.get("address")
        require(isinstance(address, str) and address in EXPECTED_ADDRESSES, "CHANGE_SCOPE")
        require(address not in seen, "DUPLICATE_CHANGE")
        seen.add(address)
        require(item.get("mode") == "managed" and item.get("provider_name") == PROVIDER, "CHANGE_PROVIDER")
        require("previous_address" not in item and "deposed" not in item, "RESOURCE_MOVE")
        change = item.get("change")
        require(isinstance(change, dict), "CHANGE_SCHEMA")
        require(change.get("actions") == ["no-op"], "ACTION_DENIED")
        require(not change.get("importing") and not change.get("generated_config"), "IMPORT_DENIED")
        require(no_unknown(change.get("after_unknown")), "UNKNOWN_VALUE")
        require(change.get("before") == old[address], "BEFORE_MISMATCH")
        require(change.get("after") == new[address] == old[address], "VALUE_CHANGE")
    require(seen == EXPECTED_ADDRESSES, "MISSING_CHANGE")
    outputs = plan.get("output_changes", {})
    require(isinstance(outputs, dict), "OUTPUT_SCHEMA")
    for output in outputs.values():
        require(isinstance(output, dict), "OUTPUT_SCHEMA")
        require(output.get("actions") == ["no-op"], "OUTPUT_CHANGE")
        require(output.get("before") == output.get("after"), "OUTPUT_CHANGE")
        require(no_unknown(output.get("after_unknown")), "UNKNOWN_OUTPUT")
    return {"policy": "PASS", "mode": "existing-noop-only", "managed_resources": len(seen)}


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise Denied("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def reject_constant(_value):
    raise Denied("INVALID_JSON_CONSTANT")


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        require(len(args) == 1, "INPUT_COUNT")
        path = Path(args[0])
        require(path.is_file() and path.stat().st_size <= MAX_BYTES, "INPUT_FILE")
        plan = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object,
                          parse_constant=reject_constant)
        print(json.dumps(evaluate(plan), sort_keys=True))
        return 0
    except Denied as exc:
        print(json.dumps({"policy": "DENY", "reason": str(exc)}), file=sys.stderr)
    except Exception:
        # Never echo exception messages, paths, JSON fragments, IDs or values.
        print('{"policy":"DENY","reason":"INPUT_OR_SCHEMA_ERROR"}', file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
