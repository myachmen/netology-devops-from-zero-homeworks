# Terraform automation acceptance — task188

## Current candidate and one design decision

[Single-owner decision package](TERRAFORM_APPLY_SINGLE_OWNER.md) is authoritative
for PR3. It supersedes task184–187 field-by-field drift review and all old
activation notes. Existing main676f985 remains Plan-only until a separately
approved squash merge. This PR has not proved real automatic Apply yet.

The active `state_reconcile_policy.py` permits fresh State/output reconciliation
only for exact14 known managed resources with every planned action no-op.
Nonzero drift/output counts (structural/status/NAT included) are not a blocker.
No per-field manifest or reconstruction of plan186 is needed. The old manifest,
strict module and optional projector remain historical, outside execution.

| Prior guard | Task188 behavior |
|---|---|
| Empty production per-field allowlists deny drift/output | Removed from active runner |
| Structural null/empty and lifecycle/path approvals | Not required for managed no-op State refresh |
| Detailed path projection can block execution | Removed from active runner; redacted counts remain |
| Any managed resource write | Still DENY |
| Unknown/sensitive/malformed/foreign/incomplete plan | Still DENY |
| Main/source/backend/tool/pins/saved-plan/TTL/locks/no retry | Preserved |

A successful state-only Apply may write S3 State and outputs. It is not a VM
start/update permission or proof of from-scratch provisioning. Owner merge is
not independent review. Existing Secrets/Variables settings are owner-reported;
actual credentials/State-write rights remain unproven until the authorized run.

## Acceptance evidence

1. Offline tests + actionlint on exact feature head; PR CI offline success,
   production skipped, no secrets/backend in PR jobs.
2. Explicit owner approval of exact head/base, protected squash merge and one
   resulting push/main run; no additional diagnostic milestone required.
3. First run validates fresh plan, records no-op14, permits observed drift/output
   refresh and executes the SAME saved plan at most once, without resource writes.
4. Native Apply0 + post-lock404 + cleanup + sanitized Summary/run screenshots.
   An empty-plan skip is not invented Apply success; a failed run gets safe STOP.
5. After successful automatic Apply, stop Terraform feature development and move
   to mandatory tag-triggered app CI/CD, then current runtime/evidence packaging.

The [original diploma](https://github.com/netology-code/devops-diplom-yandexcloud/blob/main/README.md)
allows CI/CD instead of Atlantis/Terraform Cloud and requires automatic Terraform
execution/application on main commits plus screenshots. Code/tests and old
Plan182/186 are preparation/evidence, not a claim that Apply already occurred.
No requirement for ideal zero drift, extra IAM probes, DNS/TLS/logging or a paid
rebuild is introduced. No production command, VM operation or Secret/settings
change is authorized by task188 or these documents.
