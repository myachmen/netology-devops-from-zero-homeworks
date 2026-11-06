# Terraform automation acceptance

## Task184 single-owner candidate (supersedes architecture below)

The candidate in `.github/workflows/terraform-automation.yml` replaces plan with
ONE `apply` execution job after offline checks. It remains feature/PR-only;
main is plan-only until a separately authorized merge. PRs have no production
credentials/execution. See [single-owner runbook](TERRAFORM_APPLY_SINGLE_OWNER.md)
for current policy, manual settings and evidence gates. The matching `.inert`
file is only a reference copy. Earlier variable-controlled plan/apply jobs and
independent SHA/digest approval described below are HISTORICAL, not activation
instructions for task184. They do not override the new state-only policy.

# Terraform automation: prepared, awaiting live owner gate

## Task181 superseding plan-only configuration

The active candidate uses ONLY the existing environment `terraform-plan`.
Its mode is literal `plan` in both step env and CLI, and trusted repo/push/main/
attempt1 is the job gate. No Repository Variable TF_AUTOMATION_MODE is needed.
The missing variable reported by the owner must NOT be considered configured.
The active YAML has no apply job or terraform-production reference. Sections
below describing apply/environment/variable activation are historical future
design and do not authorize creating an Environment or setting apply variables.
Task181 may publish a main-targeted PR and offline PR checks, not merge or run
Terraform. See TERRAFORM_PLAN_ACTIVATION.md for current settings/evidence gate.

Task179 prepares the existing GitHub Actions approach. Nothing here authorizes a
cloud run, main merge, workflow activation, settings edits, or apply.

## Requirement and existing evidence

[Original diploma](https://github.com/netology-code/devops-diplom-yandexcloud/blob/main/README.md)
permits CI/CD instead of Atlantis/Terraform Cloud: run and apply Terraform on
every main commit, with pipeline screenshots. Code or a local plan alone does
not satisfy this criterion.

Task178: Terraform1.15.7, provider lock0.238.0; local init/validate exited0;
one locked plan exited2. Pre-head state200/lock404 and post-lock404. No apply.
Private plan was deleted under the task's cleanup rule, and show was not run.
The cause, resource changes and drift remain UNKNOWN. Do not recreate the plan
without a new bounded cloud authorization. Task173's probe is not production
permission evidence. Local key ownership does not prove runner Secret identity.

## Candidate architecture

`ci/terraform/terraform-automation.yml.inert` is deliberately undiscoverable by
Actions. Only an owner-approved later change copies it to
`.github/workflows/terraform-automation.yml` on main. There are no path filters:
every main push triggers the pipeline. PRs run synthetic tests only. The plan and
apply jobs are mutually exclusive, controlled by `TF_AUTOMATION_MODE`:

* Missing/disabled: no backend access.
* `plan`: version, exact state/lock HEAD gates, init, validate, one locked plan,
  show for exit0 **or exit2**, sanitized summary, one post-lock HEAD, local cleanup.
* `apply`: fresh same sequence; exact main SHA approval, aggregate change digest,
  destructive/unknown/drift/outputs policy, fresh-main recheck, then **that same
  local saved plan**. No raw artifact exchange and no re-plan between approval
  check and apply. Only no-op/update on the 14 existing resource addresses is
  currently eligible; create/delete/replacement/import/move are denied.

`run_automation.py` reuses the existing provider/public-key validation, backend
fingerprints, CLI command definitions and private JSON parser from
`run_plan_only.py`. `automation_policy.py` is an additional review/apply gate;
the original stricter no-op policy/runner are retained without weakening them.
The exact 11-file source manifest includes cloud-init.yaml.tftpl. Source Git SHA,
backend and provider lock are checked. The runner rejects non-main, PR/fork/tag,
rerun and environment overrides before credential/network/process work.

All jobs use contents:read, pinned checkout/setup-terraform, wrapper:false,
fixed1.15.7, readonly provider lock, fixed backend, concurrency with cancellation
disabled and bounded stage timeouts. Concurrency is repository-local: external
Terraform writers must still be excluded and native S3 locking remains mandatory.

## Inputs, existing access and blockers

Reuse the existing three Secrets (never print values):
`TF_YC_SERVICE_ACCOUNT_KEY_JSON`, `TF_S3_ACCESS_KEY_ID`, `TF_S3_SECRET_ACCESS_KEY`.
Reuse Variables `TF_CLOUD_ID`, `TF_FOLDER_ID`, `TF_ADMIN_CIDR`, `TF_SSH_PUBLIC_KEY`.
Owner presence evidence exists historically in task162; current values,
validity and effective runner permissions are UNKNOWN. Do not create new Yandex
IAM keys or copy local administrative credentials into CI.

New non-secret controls, to configure **only after approval**:

| Control | First plan run | Apply gate |
|---|---|---|
| TF_AUTOMATION_MODE | plan | apply |
| TF_APPROVED_APPLY_SHA | unset | exact reviewed current main SHA |
| TF_APPROVED_CHANGE_SHA256 | unset | exact approved semantic change binding |
| GitHub Environment | terraform-plan | terraform-production |

The change digest binds the whole resource/drift/output change document, not
individual secret hashes. It is not proof that proposed values are safe and is
not the binary plan digest. A separate internal hash binds apply to the unchanged
saved binary in the same private directory. Review actual non-sensitive changes
under a separately approved scope before endorsing a digest. Do not approve an
opaque digest based only on an action count. A changed digest blocks apply.

GitHub Environment names do **not** themselves enforce reviewers. Before any
activation verify branch protection/rulesets, trusted-main reviews, required
reviewers for terraform-production, prevention of self-approval and deployment
branches restricted to main. If repository plan/features do not support these
controls, STOP and choose an owner-approved alternative; do not silently use an
unprotected Environment. Auto-creation of an unprotected Environment is unsafe.
Repository admin/push access does not prove these settings are configured.

The SHA/digest approval is intentionally a controlled first-apply gate. It is
not standing authority to apply every future changed commit. Full recurring
automation acceptance requires an explicitly agreed approval policy as well as
real automatic main-push run/apply evidence. The prepared restricted runner does
not support teardown/rebuild without a separate policy/permission change.

## Next SINGLE approval gate: first real CI PLAN, no apply

Request explicit permission to publish/review/merge the feature to main, copy
only the candidate workflow to .github/workflows, set mode=plan and configure
terraform-plan/terraform-production protection as agreed, and verify existing
Secret/Variable presence/ownership without exposing values. No live apply in
this gate. Approve one resulting main-push run (not dispatch/rerun), runner package
installation of pinned S3 SDK, bounded state/lock HEADs, one init/validate/locked
plan and show on exit0/2. Owner accepts the stuck-lock risk. If the source or
target is no longer agreed, STOP before backend access.

Expected evidence: immutable source/main SHA, push-event run URL, tests logs,
Terraform stage exit codes, redacted address/type/actions/counts/change digest,
state200/pre-lock404/post-lock404 and cleanup status. Screenshot Actions run graph
and job summary. Do not upload plan, show JSON, credentials, state or raw private
logs. A green plan job with PLAN_CHANGES_DETECTED is not no-op or apply success.

After this gate, separately review proposed actions and approve at most one
controlled apply, its exact SHA/digest and deployment Environment review. Capture
saved-plan apply exit0 and independent bounded postchecks under that later scope.
Only then can real automation/apply be described as verified for the diploma.

## Failures and cleanup

State missing, preexisting/unknown lock, auth failure, timeout, stale SHA, unknown
schema/resources, failed digest or denied action => STOP, no automatic rerun,
rollback/repair, force-unlock, -lock=false or manual S3 Delete. Plan exit2 in plan
mode is evidence of proposed changes, not an execution failure. Failed apply has
potentially partial side effects: inspect under a new read-only scope before
any further state-changing attempt. Rollback is **not** automatic.

Protected temporary files hold native outputs/provider file/plan only for this
run and are removed by TemporaryDirectory/finally. Secrets never enter child
argv or GitHub artifacts/logs. Only fixed error categories, stage/returncodes,
known resource addresses/types/actions/counts and one aggregate binding are
printed. The original primary error survives post-lock failure. Ordinary unlock
may leave historical lock versions/delete markers; do not physically delete them.

## Local verification and publication

Run offline only: `python3 -B -m unittest discover -s tests -p 'test_terraform_*.py' -v`
and existing actionlint against the inert candidate. These tests mock every
Terraform process, S3 HEAD and GitHub API interaction. No Terraform executable or
cloud credentials are needed. PyYAML is a test dependency; existing local package
is reused in task179. Future runner installs pinned test/SDK packages only in
separate disposable venvs under RUNNER_TEMP, without global pip/system changes.

Review branch diff against diplom-yandexcloud; infrastructure HCL/lock must be
unchanged. A feature publication/PR contains only inert templates, scripts,
tests and documentation. Do not merge or copy the active YAML in task179.
