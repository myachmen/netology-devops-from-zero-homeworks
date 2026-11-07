"""Historical task184/187 per-field policy, NOT the active Apply gate.

Exact, reviewed state reconciliation only. No I/O, CLI or network on import.

The old manifest is retained only for historical tests/traceability.
Active production policy is state_reconcile_policy.py and reads no manifest.
Tests here use synthetic data, never production state or its secret values.
"""
import hashlib
import json
import re
from automation_policy import ReviewError, require, review
from plan_policy import EXPECTED_ADDRESSES, PROVIDER, no_unknown, resources

VERSION = "state-only-v1"
# Identity/access/network changes require a different, separately reviewed profile.
PROTECTED = {"id", "name", "created_at", "folder_id", "network_id", "subnet_id",
             "network_interface", "security_group_ids", "metadata", "service_account_id",
             "listener", "http_router_id", "backend", "route", "ingress", "egress"}
PROTECTED |= {"status", "hostname", "fqdn", "zone", "scheduling_policy", "preemptible",
              "nat_ip_address", "ip_address", "ipv6_address", "external_ip", "internal_ip",
              "mac_address", "dns_record", "private_key", "token", "secret", "password",
              "credentials", "ssh_public_key", "user_data"}
NODE_KEYS = frozenset({"k8s-control-1", "k8s-worker-1", "k8s-worker-2"})
# Explicitly supported TypeMap locations, not a global null/empty equivalence.
LABEL_TARGETS = frozenset({*(f'yandex_compute_instance.k8s["{node}"]' for node in NODE_KEYS),
    "yandex_alb_backend_group.k8s_ingress", "yandex_alb_http_router.diplom",
    "yandex_alb_load_balancer.diplom", "yandex_alb_target_group.k8s_workers"})


def validate_path(kind, target, path):
    """Syntax/schema context only; protected-path authorization is separate."""
    require(kind in ("drift", "outputs") and isinstance(path, list) and len(path) <= 12, "POLICY_PATH")
    if kind == "outputs" and target == "k8s_nodes":
        require(len(path) == 2 and type(path[0]) is str and path[0] in NODE_KEYS
                and path[1] in ("internal_ip", "external_ip"), "POLICY_PATH")
        return
    require(kind != "drift" or bool(path), "POLICY_PATH")
    require(not path or type(path[0]) is str, "POLICY_PATH")
    require(all((type(x) is int and 0 <= x < 10000) or
                (type(x) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", x)) for x in path), "POLICY_PATH")
    # Labels are dynamic data, not schema tokens. No nested key approvals.
    require(not (path and path[0] == "labels") or len(path) == 1, "POLICY_PATH")


def structural_pair(kind, target, path, before, after):
    """Only exact null <-> empty TypeMap at one explicitly reviewed labels path.

    This capability authorizes nothing without a per-address manifest entry.
    Arrays, nonempty maps, labels inserts/deletes and other paths stay denied.
    """
    return (kind == "drift" and target in LABEL_TARGETS and path == ["labels"]
            and ((before is None and type(after) is dict and not after)
                 or (after is None and type(before) is dict and not before)))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def same(left, right):
    # Distinguish false from 0 and reject non-JSON values/NaN.
    return canonical(left) == canonical(right)


def manifest_gate(manifest):
    require(isinstance(manifest, dict) and set(manifest) == {"version", "drift", "outputs"}, "POLICY_MANIFEST")
    require(manifest["version"] == VERSION, "POLICY_VERSION")
    for kind, identity in (("drift", "address"), ("outputs", "name")):
        rules = manifest[kind]
        require(isinstance(rules, list), "POLICY_ALLOWLIST")
        seen = set()
        for rule in rules:
            require(isinstance(rule, dict) and set(rule) == {identity, "path", "before", "after"}, "POLICY_RULE")
            target, path = rule[identity], rule["path"]
            require(isinstance(target, str) and (target in EXPECTED_ADDRESSES if kind == "drift" else target.isidentifier()), "POLICY_TARGET")
            validate_path(kind, target, path)
            require(not any(type(x) is str and x in PROTECTED for x in path), "PROTECTED_PATH")
            scalar = all(type(rule[k]) in (str, int, float, bool, type(None)) for k in ("before", "after"))
            require(scalar or structural_pair(kind, target, path, rule["before"], rule["after"]), "POLICY_VALUE")
            if path == ["labels"]:
                require(structural_pair(kind, target, path, rule["before"], rule["after"]), "POLICY_VALUE")
            require(not same(rule["before"], rule["after"]), "POLICY_VALUE")
            key = (target, canonical(path))
            require(key not in seen, "POLICY_DUPLICATE")
            seen.add(key)
    return fingerprint(manifest)


def differences(before, after, path=(), rules=()):
    require(len(path) <= 20, "PLAN_DEPTH")
    if same(before, after):
        return []
    if isinstance(before, dict) and isinstance(after, dict):
        require(before.keys() == after.keys(), "STRUCTURAL_CHANGE")
        return [row for key in sorted(before) for row in differences(before[key], after[key], (*path, key), rules)]
    if isinstance(before, list) and isinstance(after, list):
        require(len(before) == len(after), "STRUCTURAL_CHANGE")
        return [row for i, (left, right) in enumerate(zip(before, after)) for row in differences(left, right, (*path, i), rules)]
    if isinstance(before, (dict, list)) or isinstance(after, (dict, list)):
        # Rules have already passed manifest_gate. Exact match only; no wildcard,
        # no subtree substitution, no recursive null->empty normalization.
        require(sum(rule["path"] == list(path) and same(rule["before"], before)
                    and same(rule["after"], after) for rule in rules) == 1, "STRUCTURAL_CHANGE")
    return [(list(path), before, after)]


def markers(change):
    require("before" in change and "after" in change, "CHANGE_SCHEMA")
    require(no_unknown(change.get("after_unknown")), "UNKNOWN_VALUE")
    require(no_unknown(change.get("before_sensitive")) and no_unknown(change.get("after_sensitive")), "SENSITIVE_VALUE")
    require(not change.get("importing") and not change.get("generated_config"), "RESOURCE_IMPORT")
    require(not change.get("replace_paths"), "RESOURCE_REPLACE")


def match_rules(kind, target, rows, manifest, used):
    identity = "address" if kind == "drift" else "name"
    for path, before, after in rows:
        found = [i for i, rule in enumerate(manifest[kind]) if rule[identity] == target
                 and rule["path"] == path and same(rule["before"], before) and same(rule["after"], after)]
        require(len(found) == 1, "UNAPPROVED_" + kind.upper())
        used[kind].add(found[0])


def approve(plan, manifest):
    """Return only safe binding/counts. Raises fixed categories, never values."""
    policy_digest = manifest_gate(manifest)
    summary = review(plan)
    require(not plan.get("checks") and not plan.get("deferred_changes"), "APPLY_UNCERTAINTY")
    try:
        prior = resources(plan["prior_state"]["values"]["root_module"])
        planned = resources(plan["planned_values"]["root_module"])
    except (KeyError, TypeError):
        raise ReviewError("STATE_SCHEMA") from None
    require(prior.keys() == planned.keys() == EXPECTED_ADDRESSES, "STATE_SCOPE")
    for item in plan["resource_changes"]:
        change = item["change"]
        require(change["actions"] == ["no-op"], "RESOURCE_ACTION")
        require(not item.get("previous_address") and not item.get("deposed"), "RESOURCE_MOVE")
        markers(change)
        address = item["address"]
        require(same(change.get("before"), change.get("after"))
                and same(change.get("after"), planned[address])
                and same(prior[address], planned[address]), "RESOURCE_VALUES")
    used = {"drift": set(), "outputs": set()}
    seen = set()
    for item in plan.get("resource_drift", []):
        require(isinstance(item, dict), "DRIFT_SCHEMA")
        address = item.get("address")
        require(isinstance(address, str) and address in EXPECTED_ADDRESSES and address not in seen, "DRIFT_SCOPE")
        seen.add(address)
        require(item.get("mode") == "managed" and item.get("provider_name") == PROVIDER, "DRIFT_SCOPE")
        require(not item.get("previous_address") and not item.get("deposed"), "RESOURCE_MOVE")
        change = item.get("change")
        require(isinstance(change, dict) and change.get("actions") == ["update"], "DRIFT_ACTION")
        markers(change)
        require(same(change.get("after"), prior[address]), "DRIFT_AFTER")
        rules = [r for r in manifest["drift"] if r["address"] == address]
        rows = differences(change.get("before"), change.get("after"), rules=rules)
        require(bool(rows), "DRIFT_EMPTY")
        match_rules("drift", address, rows, manifest, used)
    for name, change in plan.get("output_changes", {}).items():
        require(isinstance(name, str) and name.isidentifier(), "OUTPUT_SCHEMA")
        markers(change)
        require(change.get("actions") in (["no-op"], ["update"]), "OUTPUT_ACTION")
        rules = [r for r in manifest["outputs"] if r["name"] == name]
        rows = differences(change.get("before"), change.get("after"), rules=rules)
        require((change["actions"] == ["no-op"]) == (not rows), "OUTPUT_ACTION")
        match_rules("outputs", name, rows, manifest, used)
    # Require every approved exception to match exactly; never silently reuse an
    # obsolete manifest for a different shape of plan.
    require(all(used[k] == set(range(len(manifest[k]))) for k in used), "UNUSED_POLICY_RULE")
    return {"policy_version": VERSION, "policy_digest": policy_digest,
            "change_digest": summary["change_digest"],
            "state_changes": bool(seen or summary["output_change_count"])}
