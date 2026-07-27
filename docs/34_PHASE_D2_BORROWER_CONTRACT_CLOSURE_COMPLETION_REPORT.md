# Phase D.2 Borrower Contract Closure Completion Report

- **Report date:** 2026-07-26
- **Branch:** `feat/borrower-phase-d-contract-closure`
- **Starting HEAD:** `2d29a0af97c1198007482154fc270cdac91f5ba6`
- **Alembic head:** `20260726_0015`
- **Status:** bounded Phase D source completion; not owner acceptance, Phase F,
  deployment, controlled-pilot, production, real-data, legal/privacy/regulatory,
  accessibility, or operational approval

## Implemented source boundary

Phase D.2 completes the already approved Phase D document and final-submission
contract. It adds bounded configurable 25 MiB/file, 25-current-document, and
250 MiB aggregate plaintext limits; category and bounded `Other` description;
capability-authorized no-store draft metadata listing and explicit removal;
opaque personal-data-free object keys; exact-application row locking for
document mutations and submission; current no-store server consent retrieval;
caller-idempotent committed-result retries; and the accessible borrower
document/consent/submission/confirmation web journey.

The post-Codex reviews additionally close several fail-closed defects found before
handoff: browser handling of successful `204` document removal and uncertain
upload/removal reconciliation; document-list settlement gating while requests are
pending, failed, or unreconciled; idempotent submission convergence at the
post-row-lock boundary and after later lifecycle progression; identity-map refresh
for row locks; 30-day capability-expiry enforcement and successful document-set
activity extension; pre-parser upload size, host, origin, CSRF, and capability-cookie
controls; authorization before multipart parsing; and bounded storage/metadata
failure rollback with encrypted-object cleanup. Removal uses a durable database
pending marker before touching private object storage; object or metadata/audit
failures preserve a retry handle and block submission until cleanup completes.
Upload, removal, and submission append privacy-minimized success/failure result
evidence without filenames, object keys, capability values, document content, or
application answers. Every non-local environment requires the explicit real-data
release gate. Real-data submission also requires an explicit false-by-default
owner-approval marker on the newest active/effective consent row, and submission
independently rejects an older consent during an overlapping rollout. The server
expires the sensitive capability cookie only after durable submission success,
including an idempotent committed-result retry.

Forward migration `20260726_0015` refuses to run when borrower-document rows
already exist because their category provenance cannot be guessed. It then adds
the category/description columns and constraints, nullable removal-recovery
marker, and false-by-default consent `real_data_approved` marker. Issued migrations
`20260724_0011` through `20260726_0014` are unchanged.

## Preserved exclusions and outstanding evidence

No Phase F retention job, legal-hold operation, ingress, firewall, DNS/TLS,
backup/restore, deployment, monitoring, incident, or operational-evidence work
is included. Exact production consent remains unavailable and real-data
submission remains fail closed. A disposable PostgreSQL 16 run proved an empty
upgrade through `20260726_0015`, `alembic check`, downgrade to `20260726_0014`,
re-upgrade, and the expected false consent-release default. Existing databases
with borrower-document rows still require owner-reviewed category reconciliation;
PostgreSQL race evidence, genuine private MinIO/ClamAV ceremonies, and genuine
browser accessibility and lost-response journeys remain separate evidence gates.

Detailed command results and exact final Git status are reported in the final
implementation handoff for this worktree. No commit, push, pull request, merge, deployment,
shared-database mutation, credential, or external-service change is part of
this report.

## Validation evidence

The final review pass executed and passed:

- `npm run format` and Ruff formatting for `apps/api`;
- `npm run lint` plus `ruff check apps/api`;
- `npm run typecheck` plus `mypy apps/api/src`;
- full `npm test` (176 passed, 3 opt-in skipped) and the full quiet API pytest
  suite;
- `npm run build`;
- FastAPI OpenAPI export, TypeScript contract regeneration/formatting, and
  `git diff --check`;
- `docker compose ... config --quiet` using `.env.example`.

Focused red/green tests also exercised scanner failure, object-storage failure,
metadata-commit failure cleanup, submission snapshot-storage failure,
post-lock idempotency, lifecycle-progressed retry, recoverable object/removal
metadata failures, submission blocking while removal is pending, `204` removal
parsing, and document-list settlement gating.

Codex confirmed `20260726_0015 (head)` before implementation review. The local
Docker daemon and required PostgreSQL/MinIO/ClamAV/browser prerequisites remain
unavailable, so `make migrate-check`, genuine PostgreSQL concurrency, genuine
private-object/ClamAV ceremonies, and genuine browser keyboard/reflow/network/
lost-response evidence remain blocked acceptance gates rather than inferred
passes.
