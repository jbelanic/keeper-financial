# Phase 1B Implementation Report

**Date:** 2026-07-14<br>
**Branch:** `feature/phase-1b`<br>
**Required base/HEAD:** `8961c803dad7bbd51300d4eeab2c5c9086eacf24`<br>
**Subject:** Get Started lead inquiry, consent ownership/withdrawal, protected lead queue, attribution, redirect/booking boundaries, and generated contracts

## Outcome

Phase 1B is engineering-implemented in the working tree. The existing Phase 1A Next.js visual/accessibility system and Phase 0 FastAPI, SQLAlchemy/PostgreSQL/Alembic, Supabase identity-only, database authorization, storage, lifecycle, and audit boundaries are preserved. This is not owner/legal/privacy approval, a production launch, or an accessibility/compliance certification.

No commit, push, merge, deploy, pull request, branch creation/switch, or remote operation was performed. HEAD is required to remain at the base above; all Phase 1B work is an uncommitted working-tree delta for coordinator review.

## Delivered routes

| Method | Route | Boundary |
|---|---|---|
| POST | `/api/v1/leads` | Public strict minimal schema; server-owned consent/source; rate limited; atomic persistence. |
| GET | `/api/v1/leads` | `require_admin`; no-store; limit 1–100/default 25; offset pagination; optional lifecycle status; newest-first. |
| POST | `/api/v1/leads/{lead_id}/marketing-consent/withdrawal` | `require_admin`; no-store; marketing-only, row-locked and idempotent. |
| GET | `/api/v1/integrations/mortgage-application` | Public configuration-only `307`; optional safe mapped slug; `503` without `Location` when disabled/unsafe/unmapped. |
| GET | `/apply` | Balanced minimal-contact/full-application paths; optional safe `agent` attribution. |
| GET | `/admin/leads` | Server-protected queue; authenticated FastAPI fetch; safe page/status URL filters only. |

## LEAD-001–010 disposition

| Requirement | Disposition |
|---|---|
| LEAD-001 | Delivered: two balanced accessible `/apply` paths. |
| LEAD-002 | Delivered: only name, email, telephone, objective, preferred contact method, optional controlled agent slug, optional short message, required service acknowledgement, optional marketing, and zero-length website trap. |
| LEAD-003 | Delivered: prominent introductory and adjacent free-text warnings cover financial, identity, health, credential, and underwriting data. |
| LEAD-004 | Delivered: required in UI and API; persisted as separate server-versioned evidence. |
| LEAD-005 | Delivered: separate, optional, unchecked; server-owned immutable draft version; grant and withdrawal evidence. |
| LEAD-006 | Delivered: trusted `website_apply` source/capture source and safe hidden query attribution; API requires a published profile. |
| LEAD-007 | Delivered: backend-only redirect with HTTPS/exact-host/no-credential/query/fragment validation and optional approved mapping. |
| LEAD-008 | Delivered conditionally: real `tel:` action; book-a-call appears only when an owner-supplied HTTPS URL passes validation. No URL is currently invented. |
| LEAD-009 | Delivered: bounded protected admin queue; no notification email, export, bulk, assignment, CRM, or analytics. |
| LEAD-010 | Preserved: no borrower origination/application, financial fields, documents, underwriting, credit, lender, commission, or payroll model/flow. |

## Consent, audit, logging, and atomicity

- An immutable server registry retains the exact draft engineering service and marketing wording. Honest immutable labels are `service-contact-draft-engineering-v1`, `marketing-draft-engineering-v1`, and `privacy-notice-draft-legal-review-v1`.
- Callers cannot select consent/privacy versions; override attempts are unknown fields under `extra="forbid"`.
- `lead.created` targets the lead and contains only status/source. `marketing_consent.granted` and first `marketing_consent.withdrawn` target the consent and contain only safe capture source plus standard actor/request identifiers where applicable.
- No contact fields, message, bearer token, raw payload, or private URL/query is written to audit metadata or structured request log metadata.
- Lead, service consent, optional marketing consent, and audit writes share one transaction with explicit rollback on any persistence exception.
- Withdrawal preserves marketing `granted_at`, writes `withdrawn_at` once, never changes service acknowledgement, and creates no duplicate audit on repeat.

## Attribution, redirect, booking, and abuse controls

- Only `^[a-z0-9-]{1,100}$` query attribution is retained. It is hidden controlled form state, never a user-editable field. Invalid query values are omitted by the web; invalid API redirect grammar is rejected.
- Lead attribution requires a published `AgentProfile`. Redirect attribution independently requires an approved configuration mapping. Unknown mappings and disabled/unsafe destinations fail closed without `Location`.
- Mortgage CTAs always point to FastAPI; direct provider/destination URLs are not rendered in the CTA or page claim.
- Missing/unsafe booking configuration renders no booking link or claim. Phone/email fallback guidance is factual and contains no invented provider timing/capability.
- The direct-peer process-local limiter ignores forwarding headers, returns `429` with `Retry-After`, reopens at the window boundary, bounds tracked peers, and fails closed for new peers at capacity.

## Admin authorization and data boundary

- Both new API operations deny anonymous, unmapped identity, mapped identity-only, inactive user, candidate, wrong role, and admin without required MFA. Active verified `brokerage_admin` with AAL2 is accepted when MFA is required.
- Supabase proves identity only; FastAPI/database `require_admin` remains authoritative. The Next.js layout is server-protected and server fetch/actions obtain the token without exposing it to client props.
- Queue responses and server fetches use `Cache-Control: no-store`/`cache: "no-store"`. Only safe page/status values appear in queue URLs; there is no PII search.
- Queue output is newest-first by `created_at DESC, id DESC`; total means the complete count matching the optional status before limit/offset.

## Migration and contracts

- Issued migration `20260714_0001` was not edited.
- New revision `20260714_0002` adds useful `(created_at,id)` and `(status,created_at,id)` B-tree indexes aligned with SQLAlchemy metadata. Both the preserved normal PostgreSQL database and an isolated empty validation database reached this head with no autogeneration drift.
- FastAPI owns OpenAPI. `packages/contracts/openapi.json` and `src/generated.ts` include public lead creation, protected list/withdrawal, and redirect operations. `packages/contracts/src/index.ts` exports generated declarations and retains `PortalArea`.
- `make openapi` now exports, generates, and formats contracts. Two consecutive final runs produced identical SHA-256 values: OpenAPI `b77034dc9c746b072be40ce3e1b3034e16252e2474bb3727ec988c1648c0d71d`; generated TypeScript `7ced8cae4cd3efbfe8d4502f6451f13c6778d3e464b503195e6b8955284a81ad`.

## Validation evidence run during implementation

- Pre-change focused API baseline: 13 passed.
- Backend Phase 1B focused lead/integration slice: 53 passed before the explicit OpenAPI contract test; redirect/OpenAPI follow-up: 16 passed.
- Complete API suite before the final contract assertion/decorator delta: 69 passed, one warning.
- Focused Phase 1B web files: 24 passed. Complete web suite after the mock-harness correction: 13 files / 53 tests passed.
- Focused mypy: 32 source files, no issues. Focused web lint passed; focused web typecheck passed after correcting test typing.
- Final required validation results are recorded in the next section after documentation is complete.

## Final validation

Coordinator validation used Node `v24.18.0`, npm `12.0.1`, Python `3.14.4`, Docker `29.5.3`, and Docker Compose `v5.1.4`. An existing ignored `.env` was detected and preserved without reading or overwriting it.

### Toolchain, formatting, typing, and tests

- `npm ci`: passed; 498 packages installed, 0 vulnerabilities reported. npm reported blocked install scripts for `esbuild`, `sharp`, and `unrs-resolver`; both host and container production builds subsequently passed.
- `.venv/bin/pip install -e 'apps/api[dev]'`: passed. Both required `.venv/bin/python -m pip check` runs reported no broken requirements. `npm ls vitest next postcss` resolved Vitest `3.2.6`, Next `16.2.10`, and PostCSS `8.5.19`.
- `npm run format` and `.venv/bin/ruff format apps/api`: passed. `npm run format:check`, `npm run lint`, `npm run typecheck`, `.venv/bin/ruff check apps/api`, `.venv/bin/ruff format --check apps/api`, and `.venv/bin/mypy apps/api/src` all passed; Ruff checked 44 formatted Python files and mypy checked 32 source files.
- `npm run test`: 13 Vitest files / 56 web tests passed. `.venv/bin/pytest apps/api/tests`: 79 API tests passed with one Starlette/Python 3.14 `TestClient` dependency deprecation warning. `.venv/bin/python -m compileall -q apps/api/src apps/api/tests` passed.
- `npm run build`: passed and generated 31 Next.js pages; `/apply` and `/admin/leads` were present as dynamic routes. `docker compose build` separately built both current API and web images successfully.

### Contracts, migrations, and containers

- `make openapi`, non-empty file assertions, contract formatting, and contract typechecking passed. A second `make openapi` produced the identical hashes recorded above.
- `docker compose config --quiet`, `docker compose up -d db`, `docker compose ps`, `make seed`, `docker compose up -d`, and the final service status checks passed; database and API were healthy and the web service was running.
- Normal PostgreSQL: `alembic upgrade head` applied `20260714_0002`; `alembic current` returned `20260714_0002 (head)`; `alembic check` reported no new upgrade operations.
- Isolated empty `keeper_phase1b_validation`: create, complete `0001 -> 0002` upgrade, current-head, drift check, and final isolated-database removal all passed. The normal database/volume was not destroyed or replaced.
- Final service logs contained no application startup errors or submitted smoke PII. The preserved PostgreSQL log history records an earlier unclean shutdown and successful automatic recovery; the current database remained healthy.

### Live routes, smoke test, and dependency/security checks

- `/health` and `/health/db`: `200`, API and database healthy. Public `/` and `/apply`: `200`. Anonymous `GET /api/v1/leads`: `401`. The unauthenticated `/admin/leads` streamed response was private/no-store and carried Next's internal `307` redirect to `/auth/sign-in?returnTo=/admin`; automated protection tests remain authoritative.
- Mortgage redirect check, without `-L`: `307` with exactly `Location: https://apply.keeperfinancial.ca/`. Unsafe/disabled/query/agent cases are covered by API tests and emit no unsafe `Location`.
- The one permitted synthetic smoke submission using `phase1b@example.test` returned `201`, `new`, and `marketing_consent_recorded: false`. Its public receipt exposed no submitted contact fields. The seeded AAL2 admin retrieved the bounded queue; anonymous access remained denied.
- A database audit-metadata scan found zero occurrences of the synthetic name, email, phone, or message, and the API log scan found none. Manual source inspection found no forbidden borrower-origination field in the lead schema, service, form, or queue.
- `npm audit --audit-level=high`: passed with 0 vulnerabilities. Final pip check passed. Repository secret-pattern inspection found no private-key, AWS access-key, or bearer-token material.
- `gitleaks` scanned 4 commits and found no leaks. Trivy `0.52.2` completed a filesystem scan for HIGH/CRITICAL vulnerability, secret, and misconfiguration findings with exit code 0.
- Bandit `1.9.3` passed the high-severity gate (`-lll`) with exit code 0. Its full scan reported one medium-confidence/medium-severity B104 finding for the intentional container `0.0.0.0` bind already annotated in configuration.
- Semgrep `1.169.0`, run from a temporary isolated virtual environment, applied 452 rules across 121 tracked and untracked source targets and reported 0 findings.

### Failures encountered and resolved

Expected test-first failures were diagnosed before behavior changes: 24 initial backend acceptance failures and 8 initial frontend failures represented missing Phase 1B behavior. Fixture, Vitest hoisting, dialog focus, and formatting issues were corrected without weakening controls.

The accessibility pre-commit review initially blocked on field error identification and modal behavior. Both issues were remediated test-first; the focused suite passed 17 tests, and the final web suite passed 13 files / 56 tests together with format, lint, typecheck, and build.

During the coordinator run, `npm run typecheck` failed once because generated contracts still contained a consent UUID removed during the final data-minimization review. `make openapi` regenerated the authoritative declarations; the full typecheck, focused 47-test API contract/lead slice, focused 8-test admin web slice, full suites, builds, and deterministic contract run then passed. No failure was waived or relabelled.

Not run and not claimed: hosted Supabase/JWKS or R2 integration, production infrastructure/operations, browser-assisted manual WCAG audit, formal accessibility/privacy/security/legal certification, or deployment. PostgreSQL migration execution was verified, but no production-volume query-plan/load test is claimed.

## Owner inputs and limitations

- Owner/legal/privacy approval is still required for service, marketing, privacy, complaints, accessibility, regulatory presentation, principal-broker identity/title, and other unresolved publication claims. Current consent labels intentionally say draft/legal review.
- The final consent-withdrawal intake and identity-verification process, retention/deletion/hold periods, and production access-review policy remain owner decisions. The admin operation records an already-authorized decision; it does not invent a customer intake channel.
- An owner-approved booking provider/HTTPS URL and agent-specific redirect mappings remain optional and absent unless explicitly supplied. No save-and-return, completion-time, certification, or regulatory-validation vendor claim is made.
- No transactional-email provider, sender identity, recipients, templates, or notification/delivery policy has been approved. No email integration exists; the secure queue is the Phase 1B delivery mechanism.
- Production origins, hosting, Supabase/JWKS, R2, monitoring, incident response, backup/restore, access review, trusted-proxy topology, and multi-process/multi-replica aggregate abuse controls remain unapproved operational inputs.
- Production also needs abuse monitoring/tuning, hosted Supabase/R2 tests, production-volume PostgreSQL query-plan/load validation, and manual/browser accessibility review.
- Deferred: lead notifications/email, assignment/status mutation UI, customer self-service withdrawal, CRM, marketing automation, export/bulk action, recruitment/candidate changes, agent publication workflow, borrower application/origination/documents/underwriting, lenders, commissions/payroll, and production operations.

## Final status and diff boundary

The implementation is a coherent uncommitted Phase 1B delta only: 27 tracked files changed and 15 new files are present (42 files total). The tracked diff is 27 files, 1,209 insertions, and 137 deletions; generated/untracked files are not included in Git's tracked diff statistic. Branch is exactly `feature/phase-1b`; HEAD remains `8961c803dad7bbd51300d4eeab2c5c9086eacf24` with subject `feat: complete phase 1a development`. The issued `0001`, `.env.example`, `docs/00_PROJECT_SOURCE_OF_TRUTH.md`, and `docs/17_PHASE_1A_IMPLEMENTATION_REPORT.md` are unchanged. Neither implementation nor coordinator validation opened or printed `.env` or another secret-bearing environment file. Existing ignored `.next`, pytest/Python cache, virtualenv, and dependency directories are not part of the Git delta; no cache/build artifact is included.

Exact `git status --short --branch`:

```text
## feature/phase-1b
 M Makefile
 M README.md
 M apps/api/src/keeper_api/api/routes/integrations.py
 M apps/api/src/keeper_api/api/routes/leads.py
 M apps/api/src/keeper_api/main.py
 M apps/api/src/keeper_api/models/domain.py
 M apps/api/src/keeper_api/schemas/leads.py
 M apps/api/src/keeper_api/services/leads.py
 M apps/api/tests/test_integrations.py
 M apps/api/tests/test_leads.py
 M apps/web/app/(admin)/layout.tsx
 M apps/web/app/(public)/apply/apply-form.tsx
 M apps/web/app/(public)/apply/page.tsx
 M apps/web/app/globals.css
 M apps/web/lib/routes.ts
 M apps/web/tests/apply-form.test.tsx
 M apps/web/tests/public-pages.test.tsx
 M apps/web/tests/routes.test.ts
 M docs/07_DELIVERY_PLAN.md
 M docs/08_ACCEPTANCE_TESTS.md
 M docs/12_THREAT_MODEL.md
 M docs/13_API_AND_DATA_INVENTORY.md
 M docs/14_TEST_STRATEGY.md
 M docs/15_KNOWN_LIMITATIONS.md
 M docs/LOCAL_DEVELOPMENT.md
 M packages/contracts/src/index.ts
 M packages/ui/src/components.tsx
?? apps/api/alembic/versions/20260714_0002_lead_queue_indexes.py
?? apps/api/src/keeper_api/services/consent_registry.py
?? apps/api/tests/test_openapi_contract.py
?? apps/web/app/(admin)/admin/leads/
?? apps/web/lib/admin-leads.ts
?? apps/web/lib/lead-attribution.ts
?? apps/web/tests/admin-leads-protection.test.tsx
?? apps/web/tests/admin-leads.test.tsx
?? apps/web/tests/apply-page.test.tsx
?? docs/18_PHASE_1B_IMPLEMENTATION_REPORT.md
?? packages/contracts/openapi.json
?? packages/contracts/src/generated.ts
```

No commit, push, merge, deploy, pull request, branch creation/switch, or remote operation was performed.
