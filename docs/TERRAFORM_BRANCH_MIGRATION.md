# Terraform CI migration — preparation, not activation

This document describes the staged migration from the course branch `main` to the diploma branch `diplom-yandexcloud`.

## Status

- The source scripts and tests were copied from `main` into the diploma migration feature branch.
- Trusted ref gates in `run_automation.py`, `run_plan_only.py`, and the disabled `run_infrastructure.py` now use `refs/heads/diplom-yandexcloud`.
- The GitHub API trusted-ref check now reads `git/ref/heads/diplom-yandexcloud` and compares the result to the running/approved SHA.
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

1. Confirm the diploma branch is protected by an equivalent GitHub ruleset to `main`.
2. Confirm the `terraform-apply` Environment branch allowlist permits only the trusted diploma branch, with appropriate owner approval.
3. Run the offline test suite and review the exact diff.
4. Coordinate a single cutover so that the `main` workflow and diploma workflow cannot both write to the same state.
5. Obtain explicit owner authorization for the first live Terraform run.

Do **not** merge this preparation PR as a completed CI migration.
