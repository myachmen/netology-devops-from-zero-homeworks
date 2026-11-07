# Terraform Apply: task188 owner decision package

**PR3 is a candidate, not merged and not executed in production by task188.**
One chosen design: owner-controlled protected main merge -> automatic CI ->
fresh locked plan -> managed-noop state reconciliation -> same saved-plan Apply.
No second GitHub user or independent reviewer is required. The merge gate does
not defend against a malicious/compromised owner; trusted source/pins matter.

## Decision: check planned resource writes, not an ideal State snapshot

The original Netology assignment requires automatic Terraform execution AND
application on main commits, with pipeline evidence. Plan-only/offline tests do
not prove that criterion. Per-field null/container/lifecycle manifests introduced
in184–187 were an additional project restriction, not a diploma requirement.

The active policy is now **state_reconcile_policy.py**, profile
`managed-noop-state-refresh-v1`. It never reads `apply-policy.json` or calls the
historical `state_only_policy.py`/`drift_projection.py`. Those files/tests remain
only for traceability. Their per-field DENY results are not production gates.

| Condition | Active decision |
|---|---|
| Exact14 known managed resources, all planned actions no-op | Eligible for further safety gates |
| Observed structural/status/NAT drift, updated output map | State/output reconciliation allowed; no per-field allowlist |
| Output create/update/delete | Allowed as State/output changes, not managed cloud writes |
| Any managed create/update/delete/replace/read/forget | STOP, no Apply, no retry |
| Unknown/sensitive markers; incomplete/errored/malformed or non-applyable changed plan | STOP |
| Foreign/duplicate resources, provider mismatch, move/import/deposed, changed object ID | STOP |
| Wrong source/backend/tool/lock, stale SHA, checksum/policy/TTL mismatch | STOP |
| Truly empty plan, no drift/output changes | NO_CHANGES_APPLY_SKIPPED, no fake Apply |

`resource_changes` and `resource_drift` have different meanings in Terraform
JSON. A no-op managed plan may still update refreshed State and outputs. This
is deliberately allowed. Resource values must match refreshed prior/planned
values, IDs remain stable, and drift.after must match the refreshed state.
Sensitive/unknown markers in changes and State wrappers are still denied.
JSON schema/version, complete/errored/applyable, checks/deferred and action gates
fail closed. No new broad cloud precheck or credential probe was added.

## First main-push behavior after separate activation approval

1. Existing workflow `Terraform automation` starts on push/main. PR checks are
   offline only. Production `apply` job requires exact repo, main, push, attempt1,
   successful offline and `environment: terraform-apply`. No dispatch/rerun.
2. Source checkout/current-main and clean tree, exact11-file infrastructure
   manifest, backend/provider lock fingerprints, approved inputs and version
   are checked. Terraform1.15.7/provider0.238.0 pins remain unchanged.
3. State HEAD200 and pre-lock404; one init/validate/fresh normal locked plan
   (refresh=true, lock=true, bounded lock timeout, detailed exit0/2) and private
   Show. Init/validate/show/apply must exit0. Plan1/timeout/unknown stops.
4. Active policy validates the fresh plan. Resource writes STOP; drift/output
   changes alone do not require missing historic values or a zero-drift plan.
5. Before Apply: pre-apply-lock404, current-main/clean source, checksum of the
   same local saved binary, policy/review binding, <=900s TTL. No re-plan or
   file transport. Native stale-plan/lock checks remain authoritative.
6. One saved-plan Apply only if State/output changes exist and the plan is
   applyable. Native plan0 with drift-only may still reconcile observed State;
   native0 with planned output changes is inconsistent and stops. A truly empty
   plan skips Apply; native2 with no recorded change also stops.
7. Finally post-lock404 and private cleanup; safe Summary contains source,
   policy, native codes, managed actions/drift/output counts, heads/cleanup.
   No raw state/plan/JSON/logs/IP/credential values or artifact/cache uploads.

One production job, shared concurrency `terraform-infrastructure-s3-default`,
cancel-in-progress:false. No FIFO promise for pending GitHub runs; stale queued
SHA stops. External writers are outside repository concurrency and must not run
concurrently. Each stage has a fixed timeout; Apply900s, Plan600s, job40min.
No retry/force-unlock/reset/rollback/destroy. Runner loss may prevent finally;
report cleanup/lock uncertainty rather than claiming success.

## Explicit risk: production State can be written

**Eligible Apply can write the existing S3 State and output values**, even though
all14 planned managed actions are no-op. Native lock Put/Delete for Plan/Apply
are also writes. No-op is not a read-only backend guarantee. Provider/State-write
permissions and actual Environment credential validity are not proven offline.

Worker2 was preemptible/Stopped/no public IPv4 in OWNER_UI_REPORTED snapshot187.
If a fresh plan merely observes a new status/NAT/output while all resource
operations are no-op and other guards pass, State may record those observations.
This is not permission to start/stop/reconfigure/recreate a VM. If Terraform
proposes any such managed update/create/delete/replacement, STOP. The old plan186
was deleted; no old values were restored or assumed. No current Kubernetes or
SSH health claim is made, and worker2 must not be started to force a green CI.

## GO / NO-GO for the single owner

GO only after a separately approved activation:
- Review exact PR3 head and base from result188; latest check `offline` is success
  and production `apply` is skipped on PR. No unexpected diff or source change.
- Preserve protected main: require PR, approvals0, no force/deletion/bypass.
- Accept that Environment terraform-apply is main-only,0tags, reviewersOFF,
  waitOFF, admin bypass unchecked as OWNER_UI_REPORTED185. It and3 Environment
  Secret names already exist; do not recreate/copy credentials as a new task.
- Keep existing4 Repository Variables and3 Repository Secret copies (deletion
  HOLD185). No new mode/SHA/digest variables or IAM credentials/rights are needed.
- Approve the production State/output write risk and one resulting automatic
  execution. Environment values/permissions will first be exercised live then;
  no requirement to re-run broad IAM/S3 diagnostics before this decision.
- No competing writer; source/head/base match the approval at merge time.

NO-GO: missing known prerequisites, changed PR/base, failed offline check,
unaccepted State-write risk or absent explicit merge/execution approval.
Do not merge merely to inspect a plan. Squash merge can immediately start Apply.
Do not configure production `apply` as a required successful PR check: it must
skip there. The owner reviews and deliberately merges; no second reviewer gate.

## Exact next owner action and expected evidence

Review PR3 and explicitly approve its exact immutable head/base for ONE normal
squash merge and ONE resulting push/main run with the state-only boundary above.
Then a separately authorized executor/owner can mark ready and merge through
normal rules, without force/direct main push. This text alone is not permission.

Expected evidence: PR/main squash SHA, run event/head/attempt1, offline/Apply job
outcomes, native plan0/2 and no-op14 summary, saved-plan Apply0 if changes exist,
State/lock heads and cleanup. Redacted screenshots belong in diploma evidence.
If first run fails or outcome is uncertain, STOP with run/stage/code/lock status;
no re-run or automatic rollback. Fix only a concrete defect by new approval,
not another open-ended diagnostic series. Skip is reported truthfully, not Apply.

After the first proven automatic Apply, STOP Terraform feature work unless a
real defect exists. Next mandatory priority is tag-triggered app image build/
push, Kubernetes deployment and HTTP smoke, separately authorized. Keep final
current three-node/monitoring checks and README/evidence packaging distinct.
Do not impose zero drift, logging, DNS/TLS or repeated credential probes as
unrequested diploma blockers.

References: [Netology original](https://github.com/netology-code/devops-diplom-yandexcloud/blob/main/README.md),
[Terraform JSON](https://developer.hashicorp.com/terraform/internals/json-format),
[saved-plan Apply](https://developer.hashicorp.com/terraform/cli/commands/apply).
