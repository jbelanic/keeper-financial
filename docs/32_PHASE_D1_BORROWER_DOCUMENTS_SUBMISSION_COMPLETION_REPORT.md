# Phase D.1 Borrower Documents and Submission Completion Report

- **Report date:** 2026-07-26
- **Branch:** `feat/borrower-phase-d`
- **Starting HEAD:** `a594d371e9c995a22f22ba88a2e3409b80d83a58`
- **Alembic head after implementation:** `20260726_0012`
- **Status:** Source implementation complete for the bounded Phase D.1 API slice. This is not deployment, controlled-pilot, production, real-borrower, legal/privacy/regulatory, or accessibility approval.

## 1. Implemented scope

Phase D.1 adds borrower capability-bound document upload and borrower final submission endpoints:

- `POST /api/v1/borrower-applications/{application_id}/documents`
- `POST /api/v1/borrower-applications/{application_id}/submit`

Document upload enforces the existing borrower feature flag, exact borrower origin/CSRF controls, exact draft capability authorization, draft lifecycle, strict extension/declared MIME/libmagic/format validation, the D.1 10 MiB file limit, fail-closed scanner behavior, AES-256-GCM encryption with the borrower keyring before private object persistence, and metadata persistence in `borrower_documents`. The response returns only `{document_id, filename, size_bytes, scan_status}`.

Submission enforces exact draft capability authorization, expected revision matching, active consent-catalog version/digest matching, full typed payload validation, co-borrower coverage rules, immutable encrypted snapshot creation, consent evidence creation, `draft` to `submitted` transition, seven-year retention, and borrower capability revocation. Subsequent same-cookie submit attempts return conflict and subsequent PATCH writes are rejected.

## 2. Migration and data model

Forward migration `20260726_0012_borrower_documents_submit.py` adds:

- `borrower_documents`
- `borrower_consent_catalog`
- D.1 snapshot fields on `borrower_application_snapshots`: payload revision, schema version, ciphertext, and consent-record binding

The previous `20260724_0011` migration was not rewritten. Because owner/legal production consent wording is not available, the migration seeds the required conspicuous placeholder catalog entry:

`version="v1-draft"`, `wording_text="[PLACEHOLDER — owner legal to replace]"`, and the SHA-256 digest of that exact wording.

## 3. Validation results

Focused validation completed during implementation:

| Command | Result |
| --- | --- |
| `../../.venv/bin/pytest tests/test_borrower_applications.py::TestBorrowerPhaseDRouteIntegration -q` from `apps/api` | PASS — 11 passed |
| `../../.venv/bin/pytest tests/test_borrower_applications.py tests/test_borrower_validation.py -q` from `apps/api` | PASS — borrower application/validation subset passed |
| `../../.venv/bin/ruff check ...` on touched API/test files | PASS |
| `../../.venv/bin/alembic heads` from `apps/api` | PASS — one head, `20260726_0012` |
| `npm run test && npm run lint && npm run typecheck && npm run build` | PASS — web tests 171 passed / 3 opt-in skips, lint/typecheck passed, Next build succeeded |
| `make test && make lint && make typecheck` | PASS — repeated web tests 171 passed / 3 opt-in skips; API tests 521 passed / 11 skipped / 8 warnings; lint passed; mypy passed over 64 source files |
| `git diff --check` | PASS |

Additional schema check attempted:

| Command | Result |
| --- | --- |
| `make migrate-check` | ENVIRONMENT-BLOCKED — Docker Compose refused interpolation because `MINIO_ROOT_USER` is not set in `.env`; no migration check ran |
| `../../.venv/bin/alembic check` from `apps/api` | ENVIRONMENT-BLOCKED — configured local PostgreSQL connection failed with `psycopg.OperationalError: connection is bad`; no drift result claimed |

## 4. Residual risks

- Production consent wording remains unavailable. The seeded `v1-draft` catalog entry is a local/source placeholder only and must be replaced by owner/legal-approved wording before real-borrower submission.
- This slice does not implement borrower document download, internal review UI, queue/reassignment, legal holds, purge jobs, lender/credit-bureau integration, borrower accounts, MFA, or electronic signatures.
- Object persistence is source-validated against local/private storage and MinIO-compatible path-style code paths; this is not operational MinIO, backup/restore, ClamAV-health, TLS, ingress, or deployment evidence.
- `make migrate-check` and direct `alembic check` were blocked by local environment configuration/connectivity, so one-head evidence is confirmed but schema-drift check evidence remains pending.

## 5. Git status

No commit, push, pull request, merge, deployment, shared-database mutation, external-service change, force-push, history rewrite, or destructive operation was performed.
