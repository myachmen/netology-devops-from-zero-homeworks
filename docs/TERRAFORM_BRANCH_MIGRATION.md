# Terraform CI migration — preparation, not activation

This document describes the staged migration from the course branch `main` to the diploma branch `diplom-yandexcloud`.

## Status

- The source scripts and tests were copied from `main` into the diploma migration feature branch.
- Trusted ref gates in `run_automation.py`, `run_plan_only.py`, and the disabled `run_infrastructure.py` now use `refs/heads/diplom-yandexcloud`.
- The GitHub API trusted-ref check now reads `git/ref/heads/diplom-yandexcloud` and compares the result to the running/approved SHA.
- Permanent offline tests are defined in `.github/workflows/terraform-offline-tests.yml` and use no cloud credentials or Terraform backend.
- The proposed workflow is **inert** at `ci/terraform/terraform-automation.yml.inert`; it is **not** installed under `.github/workflows/`.
- `ci/terraform/terraform-automation.main-snapshot.yml.inert` is an unchanged historical snapshot of the previous `main` workflow.
- Historical documents under `docs/TERRAFORM_*.md` describe earlier main-based decisions and runs; their mentions of `main` are historical, **not** instructions to activate CI on `main` again.
- Legacy error category names `MAIN_METADATA` and `STALE_MAIN` are intentionally retained for backward compatibility; they now refer to the trusted diploma branch.

## Invariants

- Terraform infrastructure HCL, provider pins, `backend.tf`, `.terraform.lock.hcl`, state bucket/key, and default workspace are unchanged.
- The automation's existing state-only policy and safeguards against create/update/delete/replace of managed resources are unchanged.
- The same Terraform backend must have **only one authorized writer**. The original workflow on `main` must be retired before production activation on `diplom-yandexcloud`.
- No credentials, state, cloud resources, or GitHub Environment settings were changed by this migration patch.

## Before enabling a workflow

1. **Verified 2026-11-09:** active diploma Ruleset `26849824` matches the main branch's PR/squash/deletion/force-push protections; recheck before cutover.
2. **Current screenshot:** `terraform-apply` allows only `main` and contains three Environment secrets. Leave unchanged until the old workflow is retired; then replace `main` with `diplom-yandexcloud` (never permit both).
3. Verify the offline test suite for both push and pull_request, and review the exact diff.
4. Verify no Terraform Actions jobs are in progress; merge PR #8 to remove the old workflow from `main` and verify removal. Only then change the Environment allowlist.
5. Prepare a **separate activation PR** that moves the inert candidate to `.github/workflows/terraform-automation.yml`, keeping offline tests and all trust gates. Obtain explicit owner authorization before merging or triggering the first live run.
6. Confirm there are no competing state writers and monitor the first run.

Do **not** merge this preparation PR as a completed CI migration.
