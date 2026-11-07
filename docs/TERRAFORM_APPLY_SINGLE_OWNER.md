# Terraform Apply: single-owner candidate, task187

**Draft PR3, not merged, no live Apply authorization.** Task187 is offline code
preparation only. Main676f985 remains the working Plan-only workflow from182.
The task184 architecture remains: deliberate owner-controlled protected PR
squash merge (require PR/approvals0/no bypass/no force or deletion) plus strict
machine policy. This is not independent review and does not protect against a
malicious/compromised owner. No second account or Prevent self-review is required.

## Reused facts and unresolved data

Task186 (2026-11-07 09:51 UTC): ONE Plan exit2/Show0,14 managed no-op,9 drift
addresses,1 output change;14 sanitized records:11 structural,2 protected
network,1 unknown. Lock post404; raw plan/JSON destroyed. No exact old/new,
container contents/emptiness or three masked paths can be recovered from it.
Do not treat null->object as null->{} or guess masked paths from this code.

OWNER_UI_REPORTED 2026-11-07: preemptible k8s-worker-2 Stopped/no public IPv4;
control/worker1 Running. This is a screenshot-time observation, not independent
identity/health/trust validation or proof of the cause of all drift. The string
transitions from186 remain withheld/unknown. No VM start is authorized; start
may change NAT/costs and must not be used as a policy workaround.

## Policy contract: parser support is not authorization

Production `ci/terraform/apply-policy.json` remains byte-unchanged:
version state-only-v1, drift=[],outputs=[]. The manifest schema/version is
backwards compatible; new code is bound by its independently reviewed Git SHA.
No real allow entries or dynamic before/after were added in187.

| Case | Syntax/capability | Default / conditions |
|---|---|---|
| k8s_nodes[known-node].external_ip/internal_ip | Exact context and one of3 fixed node keys; hyphens recognized | PROTECTED_PATH; still DENY even with a rule |
| Hyphen token under another output/path, unknown node, arbitrary secret key, wildcard/traversal/dunder/negative or Boolean index | Rejected | DENY |
| Scalar exact reviewed rule | Existing state-only mechanism retained, exact typed before/after | Empty manifest grants nothing; sensitive/unknown/protected guards apply |
| labels null <-> EMPTY_MAP | Only7 fixed addresses, exact root labels path and exact direction/value rule | Dormant capability; no production rules; no implicit normalization |
| labels null -> nonempty map or array/string/Boolean | Wrong type/contents | DENY |
| Nested dynamic labels keys, key insert/delete, output containers | No subtree exceptions | DENY |
| null <-> array, array length/shape changes, ALB authority/route/VPC structure | No approved structural capability | DENY; separate type/content/path review required |
| Network/interface/NAT/IP/IDs/hostname/DNS/status/preemptible | Explicit protected tokens | DENY, not bypassed by Stopped/preemptible marker |
| Managed create/update/delete/replace/import/move, checks/deferred/unknown/sensitive | Existing strict gate | DENY |

The7 labels locations are the3 compute instances, ALB backend group, HTTP
router, load balancer and target group. Provider v0.238.0 declares labels as a
TypeMap with string elements there. No entries for virtual host/VPC/other
locations are implicitly enabled. Null/empty equivalence is NEVER recursive or
global. All rules must match and be consumed. Any nonempty/unreviewed contents
stop; no placeholders, broad allow_drift/allow_network_drift/preemptible flag.

The typed capability is exercised only with INVENTED fixtures, not recovered
production data. Only an explicitly reviewed future per-path rule can use it.
It never permits managed-resource writes: all14 actions must remain no-op.

## Preemptible lifecycle: design, not permission

Expected VM lifecycle can explain an observation but does not approve a change.
Before any separately authorized state-only reconciliation of worker2, require:

1. Fresh independently trusted VM identity (ID/created_at/private network and
   ownership baseline) and actual preemptible setting, not merely an alias.
2. A known lifecycle transition and a consistent bounded status/NAT/output
   mapping, without assuming that186 was running->stopped or an IP->null.
3. Exact private value/path review, sensitive/unknown checks and an expressly
   approved policy mechanism that avoids publishing IPs/IDs in this public repo.
4. Fresh saved plan with exact14 no-op managed actions, stable identity, source,
   lock/checksum/TTL gates; any extra network/identity action stops execution.

Current policy has NO such lifecycle exception. It denies status/NAT/output even
when a synthetic plan includes preemptible=true and stopped/no-IP. Other VMs'
identity/access/network cannot be covered by a worker2 exception. Starting VM,
trust changes, new Cloud reads/plan or changing lifecycle policy need separate
owner authorization; none occurred in187. Kubernetes readiness is UNKNOWN.

## Safe evidence projection for a FUTURE authorized run

`drift_projection.project(plan)` is a pure module, no CLI, network or file reads.
The existing runner calls it after private JSON parsing and before Apply policy,
so sanitized evidence remains in Summary even when the policy denies execution.
No raw before/after, IP, ID, metadata/SSH/credential contents are returned.

It records separate sections/counts, vetted schema paths, typed before/after,
EMPTY_MAP/NONEMPTY_MAP/EMPTY_ARRAY/NONEMPTY_ARRAY/null categories. Sensitive or
unknown masks hide shapes/categories. Dynamic labels/metadata keys and unknown
schema tokens stay masked. Recognized lowercase Compute status enums become
fixed KNOWN_RUNNING/KNOWN_STOPPED categories, never approval; unknown strings
are UNRECOGNIZED_WITHHELD. Masks override these categories as well.

Vetted examples from pinned sources:
- backend http_backend[].healthcheck[].http_healthcheck[].expected_statuses;
- virtual host route[].http_route[].http_route_action[].upgrade_types;
- VPC subnet_ids; compute status/network_interface and public k8s_nodes output.

These are schema patterns, NOT claims identifying the three masked paths186.
Unsupported patterns still mask. Shape/status classification is not exact
value review and does not create manifest entries. The existing private JSON
parser retains size/duplicate-key/NaN checks. Projection has depth/row bounds.
No stored raw plan186 is read or restored; no new Plan/Show executed in187.

Primary sources, all version v0.238.0:
- [Compute schema/Read status](https://github.com/yandex-cloud/terraform-provider-yandex/blob/v0.238.0/yandex/resource_yandex_compute_instance.go)
- [ALB backend schema/constants](https://github.com/yandex-cloud/terraform-provider-yandex/blob/v0.238.0/yandex/resource_yandex_alb_backend_group.go)
- [Virtual host schema](https://github.com/yandex-cloud/terraform-provider-yandex/blob/v0.238.0/yandex/resource_yandex_alb_virtual_host.go)
- [VPC schema](https://github.com/yandex-cloud/terraform-provider-yandex/blob/v0.238.0/yandex/resource_yandex_vpc_network.go)
- [Router labels](https://github.com/yandex-cloud/terraform-provider-yandex/blob/v0.238.0/yandex/resource_yandex_alb_http_router.go),
  [load balancer labels](https://github.com/yandex-cloud/terraform-provider-yandex/blob/v0.238.0/yandex/resource_yandex_alb_load_balancer.go),
  [target group labels](https://github.com/yandex-cloud/terraform-provider-yandex/blob/v0.238.0/yandex/resource_yandex_alb_target_group.go).

## Workflow execution contract unchanged

After a separately authorized owner merge: main push -> offline -> ONE
production job in terraform-apply -> fresh locked plan -> policy -> eligible
same private saved plan apply -> post-lock/cleanup. Workflow YAML is unchanged
in187, as are action pins, contents:read, event/repo/main/attempt1 guard,
concurrency terraform-infrastructure-s3-default/cancel-in-progress:false.
PR/fork/tag/rerun never execute production; no manual dispatch path was added.

GitHub may replace pending concurrency entries, so no FIFO promise. External
writers still require exclusion and native locking. Stale queued SHA stops.
Exact clean/current source, backend/lock manifest, binary checksum captured
before Show, versioned policy/review binding and <=900s plan TTL are rechecked
before one saved-plan apply. No additional plan between review/apply, no raw
artifact/cache, no retry/force-unlock/rollback. Empty plan0 skips fake Apply.
Private dir0700/files0600, stage timeouts and finally cleanup remain in place;
runner loss can prevent finally and must be reported UNKNOWN. A state-only
Apply still writes State/outputs and is not proof of from-scratch provisioning.

## Exact owner checklist BEFORE any future merge

No GitHub settings/Secret changes were made in187.

1. Review PR3 exact latest head and successful offline check `offline` (workflow
   Terraform automation). Production `apply` must SKIP on PR; do not require it
   as a successful PR check. Deliberate merge remains separately unauthorized.
2. Preserve main ruleset: active exact main, require PR, approvals0, no force/
   deletion, bypass empty. No second reviewer dependency.
3. Environment terraform-apply and its3 Secrets already exist per OWNER_UI185:
   main-only,0tags, reviewersOFF, waitOFF, admin bypass unchecked. Do not recreate
   them just because task184's old checklist said create. Before execution,
   verify effective saved settings/names by available metadata or owner UI;
   this repo code is not independent settings/Secret validity evidence.
4. Keep Repository copies of TF_YC_SERVICE_ACCOUNT_KEY_JSON, TF_S3_ACCESS_KEY_ID,
   TF_S3_SECRET_ACCESS_KEY:185 deletion HOLD. Main still uses terraform-plan.
   Environment copies override only the corresponding job; existing repository
   copies remain available to other trusted workflows. Delete/migrate only by
   separate approval after a proven transition and current consumer audit.
5. Preserve Repository Variables TF_CLOUD_ID, TF_FOLDER_ID, TF_ADMIN_CIDR,
   TF_SSH_PUBLIC_KEY. No new mode/SHA/digest Variables or new IAM credentials.
6. Resolve exact drift/contents/lifecycle gates; do not merge to obtain evidence.
   Local successful186 does not validate GitHub Environment credential values.
   Billing/visibility change requires checking actual Environment support;
   unsupported controls must not be simulated/bypassed.
7. Obtain explicit execution permission for reviewed SHA/policy and one fresh
   bounded execution with postchecks/cleanup. Stopped worker2 is not a request
   to start it. Do not force a green CI by changing servers or suppressing drift.

## Acceptance and next step

Offline tests/actionlint verify syntax, paths, typed structural capability,
exact match, lifecycle DENY, unknown/sensitive/malformed handling, redaction and
unchanged workflow safety. They do not prove production readiness.

One next milestone proposal: finish the bounded reconciliation policy/evidence
package after the owner chooses whether to authorize worker2 lifecycle
reconciliation; use186 as existing evidence. The unknown container contents,
three masked paths and actual old/new remain unresolved. If fresh evidence is
needed, require a separately named limit/source/timeout/cleanup authorization;
no broad IAM/S3/SSH re-diagnosis, no automatic VM start or Plan repeat.

For diploma acceptance, later collect exact PR/main/run, safe source/policy/
native codes, eligible single Apply0 and lock/cleanup evidence. Code ready,
UI-reported settings and actual automatic Apply success are separate facts.
