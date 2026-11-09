> Historical preparation record. Current PR3 activation contract is
> [task188 owner decision package](TERRAFORM_APPLY_SINGLE_OWNER.md); the old
> plan-only/inert setup below is not an instruction for the current candidate.

# Task181 — main-targeted plan-only promotion

The owner-reported main ruleset is independently confirmed active, targeting
refs/heads/main, bypass_actors=[], PR required with0 approvals and squash only,
deletion/force-push restrictions. No protection is weakened. PR1 remains draft
against diplom-yandexcloud; it is not retargeted or merged.

## Current candidate

The active candidate references existing terraform-plan (already correct in
patch180). terraform-production appears only in the historical inert full
apply design; do not create it. The blocking repository-variable condition was
removed: mode is literal plan in the step environment and command, while the
job requires push/main/exact trusted repository/attempt1. No new Variable is
needed and no apply path/job is active. Existing TF_AUTOMATION_MODE absence is
accepted, not misreported as configured.

Repository Secret references exactly match OWNER_UI_REPORTED names:
TF_S3_ACCESS_KEY_ID, TF_S3_SECRET_ACCESS_KEY, TF_YC_SERVICE_ACCOUNT_KEY_JSON.
Repository Variable references exactly match:
TF_ADMIN_CIDR, TF_CLOUD_ID, TF_FOLDER_ID, TF_SSH_PUBLIC_KEY.
Environment-level Secrets/Variables are0 per owner screenshots; repository
values are used without creating/copying credentials. Values/validity/permissions
are UNKNOWN until a separately authorized controlled run. Never reveal values.

## PR safety

The main-based patch adds this one workflow. Current main934d49f has no workflow
files, and all other added candidates remain .inert. PR events can execute only
synthetic offline tests; that job has no secrets references, Terraform setup or
runner invocation. Native Terraform/live plan runs only after push/main and
separate merge authorization. Repository-level Secrets remain a broader trust
risk if future unreviewed workflows are introduced; do not change their scope
without permission. No remote state, locks or cloud APIs are touched by PR checks.

Protection enforcement is not bypassed: request a normal reviewed PR and future
squash merge under the actual ruleset. Do not direct-push main, force, retarget
PR1, merge, dispatch or rerun a backend operation in task181.

## ONE compact remaining owner gate before merge

Do NOT resend previous screenshots. Confirm only missing facts:
1. terraform-plan protection page: after clearing administrator bypass, Save
   protection rules was actually pressed; current setting is saved. Selected
   branches/tags remains main only,0 tags; reviewers/timer remain as reported.
2. Actions > General: Actions enabled; pinned checkout/setup-terraform permitted;
   contents:read runner policy sufficient. No write/admin privilege needed.
3. Actions/Code: no other newly added active workflow can perform unintended
   cloud/apply actions on the forthcoming main push. Metadata endpoint is
   unavailable to current App; code-tree proof is rechecked before publication.

After these confirmations and successful offline PR checks, request ONE explicit
approval for the exact PR squash merge and resulting main-push Terraform CI
plan, including runner venv dependencies, bounded state/lock HEAD, one init/
validate/locked plan, private show on exit0/2, sanitized summary, post-lock404
and cleanup. Owner accepts possible stuck lock. The squash commit SHA must be
recorded after merge; feature SHA is not the final main SHA.

No apply/destroy/force-unlock or second run. Failure/unknown outcome => inspect
read-only actual status and STOP. Save run URL/event/SHA/attempt, job summary and
screenshots with no raw native logs/plan/state/Secret material. Plan-only is an
intermediate diploma milestone; protected automatic apply needs a later approval.

Prepared commit message: ci: prepare literal plan-only workflow for terraform-plan
