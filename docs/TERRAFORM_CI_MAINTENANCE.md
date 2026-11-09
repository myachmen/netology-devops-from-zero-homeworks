# Terraform CI maintenance mode (2026-11-09)

The diploma infrastructure was intentionally destroyed after assessment. The remote S3 backend remains, and a previous production run correctly stopped because its plan proposed creating 14 resources. **Do not disable the state-only apply policy to make this run green.**

- `push` and `pull_request` run offline tests only, without cloud credentials.
- `workflow_dispatch` on the trusted `diplom-yandexcloud` branch runs offline tests followed by a **manual plan** in the existing `terraform-apply` Environment. The Python runner is invoked in `plan` mode; it executes version/init/validate/plan/show and never calls `terraform apply`.
- A plan showing 14 creates is expected while the infrastructure is destroyed; the plan summary may report `PLAN_CHANGES_DETECTED` and still exit successfully. It does **not** authorize infrastructure recreation.
- Keep Environment branch allowlist restricted to `diplom-yandexcloud`, branch Ruleset active, credentials unchanged and backend state untouched.
- This workflow has **no `apply` job**. A future deployment must be designed and approved in a separate PR with explicit owner authorization.
- `terraform plan` with refresh and locking can access cloud APIs and may briefly acquire a backend lock; it does not apply the proposed resource changes. Run it only when needed, not automatically.
