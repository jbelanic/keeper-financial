# Phase B Secure Borrower Foundation Completion Report

- **Report date:** 2026-07-24
- **Branch:** `feat/borrower-secure-foundation`
- **Base/HEAD at review:** `1acf8b6f409284b9dd386cfe6403fd7c266a975d`
- **Alembic head:** `20260724_0011`
- **Purpose:** final source review, validation, living-document synchronization, and completion evidence
- **Acceptance status:** **owner-accepted on 2026-07-24** (owner, via Hermes). Source validation passed; this is not operational/production readiness.

## 1. Scope implemented

Phase B source provides:

- borrower application, encrypted payload, document metadata, consent, immutable-snapshot metadata, status-history, assignment-history, legal-hold, and SIN-reveal-audit models;
- forward migration `20260724_0011` from `20260722_0010`;
- versioned AES-256-GCM application encryption with application/purpose/revision authenticated binding and key-ID-based decryption;
- high-entropy accountless draft capability with keyed HMAC digest persistence, exact cookie/application/origin/CSRF/revision/lifecycle authorization, inactivity expiry, and no-op save semantics;
- typed versioned borrower payload validation for one primary borrower and at most one co-borrower;
- masked borrower projection, exact-assigned-agent or administrator internal authorization with AAL2, and a separate administrator/AAL2 SIN-reveal route with bounded reason and safe audit metadata;
- lifecycle, consent, snapshot, and assignment primitives needed by later coordinators;
- generated OpenAPI and TypeScript contracts.

The mounted borrower routes are limited to `POST /start`, capability-authorized `GET` and `PATCH /{application_id}`, internal `GET /{application_id}/internal`, and `POST /{application_id}/sin/reveal`. No public submission route exists. A draft lacks submission evidence and cannot be returned through the internal projection. Unit coverage of lifecycle transition logic does not expose or authorize a draft-to-submitted route.

## 2. Explicit exclusions and deferred work

Phase B does not provide or authorize:

- the Keeper-native borrower Next.js form or same-browser UI journey;
- borrower document-byte upload, validation, ClamAV/MinIO encryption/persistence, download, or cleanup;
- the Phase D immutable-snapshot/final-submission coordinator or capability revocation on successful submission;
- internal queues, assignment/reassignment operations, legal-hold operations, purge/retention jobs, or broad review UI;
- final production privacy/credit-use consent wording;
- borrower-origin DNS/TLS/ingress, production configuration, deployment, genuine browser evidence, backup/restore evidence, or operational acceptance;
- real-borrower processing, Filogix integration, credit-bureau connectivity, underwriting, lender submission, CRM, commissions, or payroll.

## 3. Final-review corrections

The final review made only bounded completion corrections:

1. corrected missing/duplicate test imports in `test_borrower_validation.py` without changing assertions;
2. formatted only the two files identified by Ruff;
3. declared the borrower capability as a real FastAPI `APIKeyCookie` dependency on capability-protected routes so generated OpenAPI contains the cookie security scheme and per-operation security requirements;
4. updated one stale migration-head assertion to `20260724_0011`;
5. added the explicit required runtime pin `cryptography==49.0.0` to `apps/api/pyproject.toml` (the worktree virtualenv already contains 49.0.0);
6. synchronized the Phase B living documents and generated contracts.

No test was weakened, no public submit handler was added, and no CORS, authorization, storage, ClamAV, environment, or lifecycle guard was relaxed.

## 4. RED/GREEN evidence

No implementation-time RED transcript was preserved for the already-substantial Phase B implementation. The final review itself observed and resolved these reproducible failures:

| Evidence | RED | GREEN |
| --- | --- | --- |
| Ruff | 10 import/symbol errors in `test_borrower_validation.py`; two files required formatting | `116 files already formatted`; `All checks passed!` |
| Targeted borrower tests | 108 passed, 1 failed because generated OpenAPI lacked the borrower cookie security scheme | 109 passed |
| PostgreSQL migration assertion | isolated upgrade reached `20260724_0011`, but one stale test expected `20260719_0008` | selected migration evidence 7 passed after correcting only the stale Phase B head assertion |

A separate opt-in PostgreSQL concurrency test remains stale because it inserts an `agent` role already created by migration `20260722_0010`. That predates Phase B and was not altered to manufacture a green result.

## 5. Validation results

### Python/API

| Command | Result |
| --- | --- |
| `.venv/bin/ruff format --check apps/api` | PASS — `116 files already formatted` |
| `.venv/bin/ruff check apps/api` | PASS — `All checks passed!` |
| `.venv/bin/mypy apps/api/src` | PASS — no issues in 63 source files |
| `.venv/bin/pytest apps/api/tests/test_borrower_crypto.py apps/api/tests/test_borrower_validation.py apps/api/tests/test_borrower_authorization.py apps/api/tests/test_borrower_applications.py` | PASS — 109 passed |
| `.venv/bin/pytest apps/api/tests` | PASS — 504 passed, 11 skipped, 8 warnings |

The 11 default skips are opt-in integration tests, not hidden failures. Synthetic data and deterministic test keys were used.

### Generated contracts

`make openapi` ran twice. Both generated `packages/contracts/openapi.json` with the identical SHA-256:

`579ac4ffe832dfbd828984ddbc7010462399d3f6d1a328e0a1c979393543a02f`

The generated contract contains the `__Host-keeper-borrower-draft` `apiKey` cookie security scheme and applies it to capability-protected read/update operations. `packages/contracts/src/generated.ts` is synchronized.

### Node/workspaces

| Command | Result |
| --- | --- |
| `npm run format:check` | PASS — all matched web/contracts/UI files use Prettier style |
| `npm run lint` | PASS |
| `npm run typecheck` | PASS |
| `npm test` | PASS — web 122 passed/3 skipped; contracts 5 passed; UI 28 passed; aggregate 155 passed/3 skipped |
| `npm run build` | PASS — contracts/UI compiled; Next.js production build completed and generated 34 routes |

### Compose, Alembic, PostgreSQL, and diff

| Command/check | Result |
| --- | --- |
| `make compose-config` | PASS using `.env.example` |
| `alembic heads` | PASS — one head: `20260724_0011` |
| isolated PostgreSQL fresh-upgrade/current/check plus upgrade/downgrade/re-upgrade tests | PASS — 7 passed; upgrade reached `20260724_0011`; `alembic check` reported no new upgrade operations |
| `git diff --check` | PASS |
| added-line security-pattern review | PASS — no hardcoded-secret assignment, shell/eval, unsafe deserialization, or formatted-SQL-execution patterns found |

`docker compose ps` could not resolve the current local Compose environment because the local `.env` does not define the required public Supabase key. `make compose-config` with `.env.example` passed, and the independently running local PostgreSQL container accepted connections and supported the isolated migration tests.

### Dependency audits

- `.venv/bin/pip-audit` is not installed, so no Python advisory scan was available.
- `npm run audit:ci` FAILED because the repository allow-list rejected findings in 17 dependency packages. Phase B changed no Node dependency manifest or lockfile. This result was not hidden or “fixed” by weakening audit policy.

## 6. Security and privacy review

Confirmed source evidence:

- raw capabilities are returned only as host-only secure HTTP-only same-site cookies; keyed digests persist;
- capability-protected routes have explicit generated OpenAPI cookie security declarations;
- origin, host, CSRF, application ID, revision, lifecycle, and inactivity boundaries fail closed;
- AES-256-GCM uses per-write nonces and authenticated application/purpose/revision context;
- plaintext borrower payload and raw SIN are not persisted in ordinary model fields or returned to borrower draft reads;
- internal access requires active role/relationship authorization and AAL2; cross-application and wrong-assignment access is denied;
- SIN reveal is separate, bounded, and safely audited without recording the SIN or reveal reason text;
- no public submit route exists and draft access is not revoked before the future submission coordinator establishes durable evidence;
- no borrower bytes are written to object storage in Phase B;
- generated errors and denial responses are bounded and avoid capability/ciphertext/SIN disclosure.

Operational evidence remains pending for key custody/rotation/recovery, exact production consent, DNS/TLS/ingress, CORS/browser behavior, abuse capacity, monitoring, backup/restore, retention/purge, incident response, and real release configuration.

During validation, an initial failed host-side PostgreSQL connectivity attempt allowed the SQLAlchemy traceback to include local connection parameters in the private tool/session output. The value is not reproduced here. If that local credential is not disposable development-only material, rotate it before further use. The subsequent successful checks suppressed connection-value output.

## 7. Living-document updates

Updated current-state wording in:

- `AGENTS.md`
- `docs/03_ARCHITECTURE_BASELINE.md`
- `docs/04_SECURITY_PRIVACY_COMPLIANCE_BASELINE.md`
- `docs/05_DOMAIN_MODEL_AND_LIFECYCLES.md`
- `docs/07_DELIVERY_PLAN.md`
- `docs/08_ACCEPTANCE_TESTS.md`
- `docs/11_ENVIRONMENT_VARIABLES.md`
- `docs/12_THREAT_MODEL.md`
- `docs/13_API_AND_DATA_INVENTORY.md`
- `docs/14_TEST_STRATEGY.md`
- `docs/15_KNOWN_LIMITATIONS.md`
- `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md`

Historical reports were not changed.

## 8. Files changed in the Phase B worktree

### Source, migration, schemas, services, and configuration

- `apps/api/pyproject.toml`
- `apps/api/alembic/versions/20260724_0011_borrower_application_tables.py`
- `apps/api/src/keeper_api/api/router.py`
- `apps/api/src/keeper_api/api/routes/borrower_applications.py`
- `apps/api/src/keeper_api/core/config.py`
- `apps/api/src/keeper_api/models/__init__.py`
- `apps/api/src/keeper_api/models/borrower.py`
- `apps/api/src/keeper_api/schemas/borrower_internal.py`
- `apps/api/src/keeper_api/schemas/borrower_payload.py`
- `apps/api/src/keeper_api/services/borrower_applications.py`
- `apps/api/src/keeper_api/services/borrower_authorization.py`
- `apps/api/src/keeper_api/services/borrower_crypto.py`

### Tests

- `apps/api/tests/test_borrower_applications.py`
- `apps/api/tests/test_borrower_authorization.py`
- `apps/api/tests/test_borrower_crypto.py`
- `apps/api/tests/test_borrower_validation.py`
- migration expectation updates in `test_agent_role_configuration_migration.py`, `test_candidate_remediation_migration.py`, `test_phase1e_migration.py`, `test_phase1f_schema_drift_migration.py`, and `test_policy_gate_repair_migration.py`

### Generated contracts and documentation

- `packages/contracts/openapi.json`
- `packages/contracts/src/generated.ts`
- the living documents listed in section 7
- this completion report

## 9. Residual risks, blockers, and owner decisions

1. **Owner-accepted on 2026-07-24** (owner, via Hermes). This report is the acceptance evidence; it is source validation, not operational/production readiness. Remaining items below are deferred to later phases or owner decisions.
2. `.env.example` and Compose do not yet expose the typed Phase B borrower settings required by the approved prompt. Both feature gates default off; do not deploy or enable real data. This must be resolved in an owner-approved configuration step.
3. The owner-approved integration plan exists at `.hermes/approved-borrower-application-integration-plan.md`; the prompt-required repository copy at `docs/29_BORROWER_APPLICATION_INTEGRATION_PLAN.md` is absent. Document number 29 remains reserved for that plan copy; this completion report uses number 30. The owner must decide whether to add the missing approved-plan copy before publication.
4. The Node audit policy currently fails on 17 vulnerable dependency packages. Dependency remediation is outside this Phase B source-only finish and remains required before release acceptance.
5. One pre-existing opt-in PostgreSQL concurrency test assumes the `agent` role does not exist, conflicting with migration `20260722_0010`. It remains red when the entire opt-in migration suite is forced on and should be repaired in its owning onboarding-completion scope.
6. Python advisory scanning was unavailable because `pip-audit` is not installed.
7. The untracked pre-existing path `20260724_171935_6054e8` was not opened or modified during this review. It is unrelated to Phase B source and requires owner disposition before any commit.
8. Final submission, documents, UI, production consent, deployment, browser evidence, operational evidence, and later lifecycle/retention work remain pending.
9. The local development database credential exposed only in private validation output should be rotated if it is not disposable.

## 10. Git status at report creation

No commit, push, merge, deployment, external-service change, or other worktree operation was performed. The expected final status consists of the Phase B modified/untracked source, generated contracts, living-document updates, this untracked report, and the untouched pre-existing untracked `20260724_171935_6054e8` path. The exact machine-readable status was re-run after writing this report and is included in the final reviewer response.
