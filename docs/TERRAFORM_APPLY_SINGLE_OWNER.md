# Terraform Apply: single-owner candidate, task184

This is code preparation, not authorization to merge or execute Terraform.
Task182 proved automatic Plan. Task183 designed Apply but assumed a second
reviewer. Task184 explicitly replaces that assumption: one owner reviews the
PR and deliberately squash merges to protected main (PR required, approvals0,
force/deletion blocked, no bypass). This is **owner-controlled merge approval**,
not independent review and not protection against a malicious/compromised owner.
No second account, required reviewer or Prevent self-review is required.

## Execution contract after a separately authorized merge

`main push -> offline -> one terraform-apply job -> fresh locked plan -> exact
state-only policy -> same private saved-plan apply -> lock/cleanup evidence`.

Only trusted repository/push/refs/heads/main/attempt1 is admitted in both YAML and
Python. PR/fork/tag/dispatch/rerun never invokes production. No path filters;
every main commit starts orchestration, including doc commits. There is one
production job, no duplicate standalone plan workflow. Shared concurrency is
`terraform-infrastructure-s3-default`, cancel-in-progress:false. It serializes
repository jobs, not external writers; stale queued main SHA stops. GitHub can
replace pending concurrency entries: do not promise FIFO/execution of every
intermediate queued commit. Native S3 locks and no external concurrent writers
remain necessary. Recheck current main before applying; source freshness is an
observation, not an atomic lock preventing later GitHub merges.

`TF_APPLY_AUTHORIZATION: OWNER_MERGED_STATE_ONLY_V1` is a literal code contract,
NOT independent human approval, a secret, or an extra repository variable.
The approval is the separately authorized owner merge of exact reviewed code.
The manifest comes from that same clean SHA and is versioned `state-only-v1`.
Squash SHA need not be guessed in a pre-merge Variable. Old external
TF_APPROVED_APPLY_SHA / TF_APPROVED_CHANGE_SHA256 activation is not used by this
runner. Existing old inert helpers are historical and are not activated.

### Deny-by-default state policy

`ci/terraform/apply-policy.json` currently contains **empty drift/output lists**.
`state_only_policy.py` requires exact14 known managed addresses, complete/schema
and version checks, stable refreshed/planned values and no resource writes.
Every resource action must be no-op; update/create/delete/replace/import/move,
unknown or sensitive markers, check/deferred uncertainty stop execution.
Drift may only be exact update of a reviewed scalar on the same resource; each
changed path plus before/after must match one reviewed rule, with no wildcard
or subtree exceptions. Structural insert/delete and protected identity/network/
access paths are denied. Output changes also require exact reviewed scalar
rules and no unknown/sensitive markers. All rules must be consumed; unused rules
stop rather than silently carrying old approval into a different plan.

**Historical no-op14/drift9/output1 is not permission. Real paths/values are
UNKNOWN. This production candidate will refuse that shape until narrowly
reviewed safe exceptions exist.** Do not add inferred paths or real secrets to
the manifest. Before/after in a future rule may contain only expressly reviewed
non-sensitive data; when that cannot be established, STOP. The positive tests
use artificial fields/values; they are not production policy entries.

Strict marker checks can also reject provider-marked sensitive unchanged
values; the profile is deliberately conservative, not guaranteed live-ready.
Policy is a client-side boundary; it does not replace IAM. No-op here means no
planned managed-resource write, not absence of refreshed state/output writes.
A reconciliation apply does not prove recreation from scratch.

### Same plan / TTL / STOP

Private directory0700/files0600; fixed backend/provider lock and source manifest;
clean exact checkout/current-main checks before execution and immediately before
apply. Version1.15.7; locked fresh plan with refresh=true, bounded lock timeout,
private -out and native detailed exit0/2, private show JSON. Binary checksum is
captured immediately after plan, before show. Before apply, recheck checksum,
clean source/current-main, versioned policy hash, exact reviewed plan binding,
manifest and TTL<=900 seconds (conservative: clock starts before plan). No second
plan, transport to another job, raw artifact/cache or printed native values.

Only exit2 AND approved state-only changes can reach one saved-plan apply.
Exit0 with no changes returns NO_CHANGES_APPLY_SKIPPED; do not fake an Apply for
screenshots. Contradictory exit/JSON stops. Native returncode2 stays2 in safe
Summary; the Python successful step may itself exit0. Source/digest binding is
not permission to apply unreviewed changes.

Pre-state HEAD200/pre-lock404, pre-apply-lock404 and finally post-lock404 are
mandatory. Any unknown/non404 lock stops; no forced unlock. Terraform's native
lock/stale-plan checks remain authoritative if state changes in between probes.
Timeout/error/uncertain apply outcome: STOP, no rerun/rollback/restore/destroy.
One apply stage has900s timeout, job40min; plan600s, lock timeout60s. Temp cleanup
in finally removes only own private files, including failed paths. Loss/kill of
runner may prevent finally; don't claim guaranteed cleanup in that case.

Only redacted counts/fixed categories, aggregate digests, source SHA, native
command records, heads/cleanup go to Job Summary. Never publish raw plan/show/
state/logs/secret values. No Terraform or cloud call was made in task184.

## Exact owner UI checklist BEFORE a future merge

No settings changes were made in task184. This checklist is a separately
approved owner operation, not an instruction to activate now.

1. Review this PR and offline diff/tests. Do not merge until a new task grants
   the one production plan and any permitted saved-plan apply. Current live
   readiness is BLOCKED by unknown drift/output paths and empty allowlists.
2. Settings -> Rules -> existing Protect main branch: active exact main,
   require PR, approvals **0**, no force/deletion, bypass empty. Do not introduce
   approvals1 or a second-user dependency. If a required check is configured,
   use the actual PR check context **offline** (workflow Terraform automation),
   verify it in PR Checks; do NOT require the production `apply` job on PRs,
   because it must skip there. Do not bypass existing protection.
3. Settings -> Environments -> create **terraform-apply**. Deployment branches
   and tags -> Selected -> branch main only, no tag rules. Required reviewers
   OFF, wait timer OFF; administrator bypass disabled. Save and independently
   verify. Leave terraform-plan unchanged. Current implementation repository
   is public; if visibility/tariff changes, verify Environment branch/secrets
   support before activation rather than assuming unsupported controls exist.
4. As a separate authorized owner operation, move/re-scope the existing three
   execution credentials into terraform-apply environment Secrets with the same
   names: TF_YC_SERVICE_ACCOUNT_KEY_JSON, TF_S3_ACCESS_KEY_ID,
   TF_S3_SECRET_ACCESS_KEY. Reuse values securely; no new keys or IAM grants.
   Environment secrets override same-name repository values for this job, but
   repository copies remain available to other trusted workflows until removed
   by an explicitly approved migration. Do not claim complete isolation until
   their consumers/copies are reconciled. No secret values in screenshots.
5. Preserve four existing Variables (repository scope is sufficient):
   TF_CLOUD_ID, TF_FOLDER_ID, TF_ADMIN_CIDR, TF_SSH_PUBLIC_KEY. No new approval
   SHA/digest/mode Variables. Names/references can be inspected without values.
6. Actions permissions contents:read; SHA-pinned checkout/setup (existing pins),
   no PR approve/write permission. No new cloud permissions. Current successful
   Plan is not proof of effective Apply/state-write rights; future execution
   requires those to be verified within its separately approved scope.
7. Save sanitized screenshots/read-back: main ruleset, main-only environment,
   no reviewers, disabled bypass, names only of credentials/variables. A missing
   environment can be auto-created without protection by Actions: do not merge
   first and configure it later. Gate is the owner merge plus policy, not the
   Environment name alone.

Repository Secrets remain a limitation of the existing design: other trusted
workflows can reference them. Main protection/owner review must include all
workflow, helper, manifest and test changes. No independent-review security is
claimed. Don't broaden IAM/network/backend permissions to make the run green.

## Validation and next delivery step

Run locally, offline (no dependencies installed by task184):

    python3 -B -m unittest discover -s tests -p 'test_terraform_*.py' -v
    actionlint .github/workflows/terraform-automation.yml

Tests mock all subprocess/API operations in runtime simulations; synthetic
positive fixtures are separate from empty production policy. Negative coverage
includes destructive/resource updates, imports/moves, unknown/sensitive data,
missing/unapproved rules, schema/state mismatch, stale SHA, TTL/checksum/policy
binding, pre/post lock uncertainty, raw-value canary leakage, apply errors and
no retry. Existing historical runbooks remain evidence, not live instructions;
this task184 contract supersedes their obsolete activation architecture.

One next authorization: finish safe real drift/output review under explicitly
bounded fresh-plan permission, owner UI configuration, then deliberate merge
of exact reviewed candidate if/when eligible. If unapproved paths remain, STOP
and report categories without raw values; no automatic second plan. This PR
alone does not authorize that operation or prove automated Apply acceptance.

End-to-end evidence after a separately authorized run: PR/squash SHA + main-push
run attempt1, exact policy version/hash, native plan exit/action counters,
apply invoked once/exit0 if eligible (or truthful skip/STOP), lock404 and cleanup,
and separately scoped postchecks. Preserve original diploma screenshots and
links. Code-ready, UI-ready and real Apply-success are separate milestones.
