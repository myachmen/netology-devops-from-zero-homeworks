"""Historical optional task187 evidence helper; not in the task188 Apply path.

Bounded evidence projection, never approval. Pure offline API, no CLI/I/O.

Schema patterns: Yandex provider v0.238.0 yandex/resource_yandex_*.go;
resource_yandex_alb_backend_group.go: expectedStatusesSchemaKey/healthCheck;
resource_yandex_alb_virtual_host.go: route/http_route_action/upgrade_types;
resource_yandex_vpc_network.go: subnet_ids; compute_instance.go: status/labels.
Public outputs: this repository's outputs.tf. Unknown schema tokens stay masked.
No raw before/after values are returned, including recognized status strings.
"""
from automation_policy import require, review
from plan_policy import EXPECTED_ADDRESSES, PROVIDER
NODE_KEYS = frozenset({"k8s-control-1", "k8s-worker-1", "k8s-worker-2"})

INDEX = object()
MISSING = object()
ROOTS = (("id",), ("name",), ("created_at",), ("labels",), ("metadata",))
COMPUTE = ROOTS + (("status",), ("network_interface", INDEX, "nat_ip_address"),
    ("network_interface", INDEX, "ip_address"), ("network_interface", INDEX, "ipv6_address"),
    ("scheduling_policy", INDEX, "preemptible"))
BACKEND = ROOTS + (("http_backend", INDEX, "healthcheck", INDEX, "http_healthcheck", INDEX, "expected_statuses"),)
VIRTUAL_HOST = (("authority",), ("route", INDEX, "http_route", INDEX, "http_route_action", INDEX, "upgrade_types"))
NETWORK = ROOTS + (("subnet_ids", INDEX), ("default_security_group_id",))
OUTPUTS = tuple((node, leaf) for node in sorted(NODE_KEYS) for leaf in ("internal_ip", "external_ip"))


def kind(value):
    return "missing" if value is MISSING else {type(None): "null", bool: "boolean", int: "number",
        float: "number", str: "string", dict: "object", list: "array"}.get(type(value), "unknown")


def shape(value):
    if type(value) is dict: return "EMPTY_MAP" if not value else "NONEMPTY_MAP"
    if type(value) is list: return "EMPTY_ARRAY" if not value else "NONEMPTY_ARRAY"
    return kind(value).upper()


def diffs(before, after, path=()):
    require(len(path) <= 20, "PROJECTION_DEPTH")
    if type(before) is dict and type(after) is dict:
        for key in sorted(before.keys() | after.keys()):
            yield from diffs(before.get(key, MISSING), after.get(key, MISSING), (*path, key))
    elif type(before) is list and type(after) is list and len(before) == len(after):
        for index, (left, right) in enumerate(zip(before, after)):
            yield from diffs(left, right, (*path, index))
    elif type(before) is not type(after) or before != after:
        yield path, before, after


def marked(mask, path):
    for token in path:
        if mask is True: return True
        if mask is None or mask is False: return False
        if type(mask) is dict: mask = mask.get(token, False)
        elif type(mask) is list and type(token) is int and 0 <= token < len(mask): mask = mask[token]
        else: return True
    if mask is None or mask is False: return False
    if type(mask) is dict: return any(marked(x, ()) for x in mask.values())
    if type(mask) is list: return any(marked(x, ()) for x in mask)
    return True


def schema_patterns(section, alias):
    if section == "output_changes": return OUTPUTS if alias == "k8s_nodes" else ()
    if alias.startswith("yandex_compute_instance."): return COMPUTE
    if alias.startswith("yandex_alb_backend_group."): return BACKEND
    if alias.startswith("yandex_alb_virtual_host."): return VIRTUAL_HOST
    if alias.startswith("yandex_vpc_network."): return NETWORK
    return ROOTS


def path_projection(path, patterns):
    def matches(prefix, pattern):
        return len(prefix) <= len(pattern) and all(
            (type(x) is int and 0 <= x < 10000) if y is INDEX else type(x) is str and x == y
            for x, y in zip(prefix, pattern))
    result = []; opaque = False
    for index, token in enumerate(path):
        if opaque: result.append("<withheld-key>")
        elif any(matches(path[:index+1], pattern) for pattern in patterns): result.append(token)
        else: result.append("<unvetted-key>"); opaque = True
    return result, not opaque


def status_category(value):
    # Provider Read lowercases Compute API enum (v0.238.0 compute_instance.go).
    if value is None: return "NULL"
    if type(value) is not str: return "UNRECOGNIZED_TYPE"
    return {"running": "KNOWN_RUNNING", "stopped": "KNOWN_STOPPED"}.get(value, "UNRECOGNIZED_WITHHELD")


def project(plan):
    summary = review(plan)
    rows = []
    for section in ("resource_changes", "resource_drift", "output_changes"):
        entries = plan.get(section, {} if section == "output_changes" else [])
        items = entries.items() if section == "output_changes" else ((x.get("address"), x) for x in entries)
        for target, item in items:
            if section == "output_changes":
                alias = "k8s_nodes" if target == "k8s_nodes" else "<unreviewed-output>"
                change = item
            else:
                require(isinstance(item, dict) and target in EXPECTED_ADDRESSES
                        and item.get("mode") == "managed" and item.get("provider_name") == PROVIDER, "PROJECTION_SCOPE")
                alias = target; change = item.get("change")
            require(isinstance(change, dict) and "before" in change and "after" in change, "PROJECTION_SCHEMA")
            for path, before, after in diffs(change["before"], change["after"]):
                projected, vetted = path_projection(path, schema_patterns(section, alias))
                sensitive = marked(change.get("before_sensitive"), path) or marked(change.get("after_sensitive"), path)
                unknown = marked(change.get("after_unknown"), path)
                private_map = bool(path and path[0] in ("metadata", "labels"))
                structural = any(kind(x) in ("missing", "object", "array") for x in (before, after))
                network = (section == "output_changes" and alias == "k8s_nodes") or bool(path and path[0] in (
                    "id", "name", "created_at", "network_interface", "subnet_ids", "default_security_group_id", "scheduling_policy"))
                status = alias.startswith("yandex_compute_instance.") and path == ("status",)
                if sensitive or (path and path[0] == "metadata"): category = "SENSITIVE_WITHHELD"
                elif unknown or not vetted: category = "UNKNOWN"
                elif network: category = "PROTECTED_IDENTITY_OR_NETWORK"
                elif structural: category = "STRUCTURAL_CHANGE"
                else: category = "UNKNOWN"
                row = {"section": section, "alias": alias, "path": projected,
                    "before_type": kind(before), "after_type": kind(after), "sensitive": sensitive,
                    "unknown": unknown, "structural": structural, "category": category,
                    "values": "WITHHELD", "evidence_only": True}
                # Container shape is safe only at vetted schema locations; never
                # expose dynamic map keys/content or sensitive/unknown shapes.
                shape_ok = vetted and not sensitive and not unknown and (not private_map or path == ("labels",))
                row["before_shape"] = shape(before) if shape_ok else "WITHHELD"
                row["after_shape"] = shape(after) if shape_ok else "WITHHELD"
                if status:
                    row["before_status_category"] = status_category(before) if not sensitive and not unknown else "WITHHELD"
                    row["after_status_category"] = status_category(after) if not sensitive and not unknown else "WITHHELD"
                    row["lifecycle_note"] = "OBSERVED_STATE_ONLY_NOT_VM_WRITE_PERMISSION"
                rows.append(row); require(len(rows) <= 2000, "PROJECTION_SIZE")
    return {"projection_version": "schema-v0.238.0-evidence-v1", "evidence_only": True,
        "managed_resources": summary["managed_resources"], "actions": summary["actions"],
        "drift_count": summary["drift_count"], "output_change_count": summary["output_change_count"], "rows": rows}
