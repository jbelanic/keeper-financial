# Phase 0 Implementation Report

Date: 2026-07-14

## Outcome

The repository contains a Next.js/React/TypeScript web foundation, FastAPI modular monolith, PostgreSQL/SQLAlchemy/Alembic data foundation, local Compose and Supabase CLI configuration, application-owned authorization, private storage adapters, API contract generation, accessible shells/components, structured logging, append-oriented audit service, synthetic local seed, and security-focused tests.

Phase 0 remains a foundation. It is not production-ready and does not claim legal or regulatory compliance. It stays inside the source-of-truth boundary: no mortgage deals, borrower underwriting data, borrower document vault, lender submission, commission/payroll, custom signing, or fabricated provider integration.

## Remediation outcome

- Corrected valid lead fixtures so consent persistence tests exercise accepted syntactic email addresses; 29 API tests now pass.
- Added an always-on, bounded, thread-safe direct-peer lead limiter with `429`/`Retry-After`, fail-closed client-capacity behavior, and no trust in spoofable forwarding headers.
- Added a zero-length hidden automation-trap field to the strict lead schema and web form. Filled traps and unknown fields are rejected and never persisted.
- Added append-oriented `marketing_consent.granted` audit evidence tied to the consent record and request ID.
- Fixed Ruff `RUF012`, formatted the API/web/UI sources, constrained Prettier to source paths instead of generated `.next` output, and made Vitest's automatic JSX transform explicit.
- Added a repository-root mypy configuration so the exact root command applies strict checking and the scoped boto3 `import-untyped` exception.
- Preserved and reviewed `package-lock.json`. Vitest is pinned to the supported 3.2.6 patch. Next remains on 16.2.10 with a narrow PostCSS 8.5.19 override instead of the unsafe audit-suggested Next downgrade.

## Security baseline review

| Baseline area | Executable Phase 0 control | Honest residual |
|---|---|---|
| Data classes and minimization | Domain/API inventory, no borrower application model, strict minimal lead allow-list, sensitive-term rejection, visible free-text warning | Approved production copy and retention execution remain. |
| Consent | Required service acknowledgement, separate optional marketing record, versioned wording/privacy notice, capture source/timestamp, marketing-grant audit event | Final wording, withdrawal API/process, and retention policy remain. |
| Candidate privacy | Candidate data/document models are private and access-controlled | The application flow and required pre-submission privacy disclosure do not exist yet and must ship together. |
| Authentication | Supabase identity boundary, asymmetric issuer/audience verification, verified local identity, local dev-auth confinement, nonlocal admin-MFA requirement | Managed provisioning, password-reset UX, session revocation/offboarding integration, real JWKS tests, and candidate MFA policy remain. |
| Abuse controls | Always-on bounded per-process direct-peer lead limiter, spoof resistance, hidden-field trap, tests | Multi-replica aggregate/edge control, trusted-proxy design, monitoring, and tuning remain pre-production work. |
| Authorization | Server-side deny-by-default role, resource, ownership, lifecycle, publication, and document checks | Future endpoints require the full adversarial matrix; public record queries are not implemented. |
| Audit and logging | Append-oriented audit service for implemented high-risk changes; safe request logging excludes bodies, headers, tokens, free text, and object URLs | Dedicated DB privileges, immutable export/tamper evidence, centralized redaction review, and unimplemented-event workflows remain. |
| File security | Private local/R2 adapters, random keys, size/MIME allow-list, quarantine gate, per-request authorization/audit, private no-store/nosniff download | Upload API, magic-byte/extension validation, malware scanner, deletion/retention, bucket review, and R2 integration remain. |
| Retention | Required categories are documented; no final legal periods are hard-coded | Approved schedules, deletion jobs, holds, exports, and incident retention remain. |
| Security operations | Threat model, code/static checks, lockfile/integrity review, tests, fail-closed nonlocal configuration | Secret scanning, code-review enforcement, backup/restore, incident response, access/MFA/log/storage reviews, vendor/privacy registers, and vulnerability operations remain. |
| Accessibility | Semantic structure, labels/instructions, error summary, focus styles, keyboard-native controls, responsive layout, non-colour status text | Browser automation, manual WCAG 2.1 AA audit, contrast/content review, and document alternatives remain. |
| Regulatory identity/advertising | Placeholder regulatory values are configuration-driven; no database-backed public profile/posting query exists; profile lifecycle requires approval evidence | Owner/legal identity, claims/content approval, and publication-filter query tests remain. |

## Architecture decisions retained

- One Next.js App Router web application and one FastAPI modular monolith.
- PostgreSQL is authoritative for roles, relationships, lifecycle, consent, and audit; Supabase proves identity only.
- Local filesystem storage is local-only; nonlocal configuration requires private R2-compatible storage and prohibits public object URLs.
- FastAPI OpenAPI export plus `openapi-typescript` generation remains the contract boundary.

## Validation status

| Command/check | Remediation result |
|---|---|
| `.venv/bin/pytest apps/api/tests` | Pass: 29 tests. |
| `.venv/bin/ruff check apps/api` | Pass. |
| `.venv/bin/ruff format --check apps/api` | Pass: 41 files already formatted. |
| `.venv/bin/mypy apps/api/src` | Pass: 31 source files. |
| `npm ci` | Pass: clean install completed successfully. |
| `npm ls vitest next postcss` | Pass: installed dependency tree confirms Vitest 3.2.6, Next 16.2.10, and PostCSS 8.5.19. |
| `npm test` | Pass: 5 tests under Vitest 3.2.6, including the ApplyForm test. |
| `npm run lint` | Pass for web and UI. |
| `npm run typecheck` | Pass for web, contracts, and UI. |
| `npm run format:check` | Pass for web, contracts, and UI; generated `.next` output is excluded by source-scoped scripts. |
| `npm run build` | Pass: Next 16.2.10 production build and 21 routes. |
| `npm audit` | Pass: live registry advisory audit reports zero vulnerabilities. |
| Lockfile validation | Pass: lockfile v3, successful clean install, registry integrity on every registry package, only expected workspace links, and four reviewed install-script packages. |
| Alembic | Pass: `alembic upgrade head` and `alembic current` succeeded against PostgreSQL at revision `20260714_0001`. |
| Compose | Pass: `docker compose config`; API and web images built successfully; `docker compose up -d` started healthy PostgreSQL and API services plus the web container. |
| Supabase | Later reconciliation (2026-07-16): the tracked local stack starts via `npx supabase` 2.109.1; Auth is healthy; JWKS returns HTTP 200 with exactly one ES256 key. |

This table retains the Phase 0 application-test evidence while recording the later Auth reconciliation above. Hosted Supabase and hosted R2 are no longer deployment targets. The current local Docker deployment has separate live evidence in `docs/LOCAL_DEVELOPMENT.md`; backup/restore, host hardening, real mail delivery, approved malware scanning, and release approval remain unresolved and are not converted into passes by local validation.

## Owner decisions still required

- Approved legal brokerage name, licence number, principal broker identity/title, and public regulatory footer.
- Final font/image licensing, brand tokens, navigation labels, mobile interpretation, and accessibility/content approval.
- Hosting, private R2 account/bucket, transactional email, booking, mortgage application, and established e-signature providers.
- Mortgage provider allowed host/base URL and whether approved agent-specific links are supported.
- Retention periods and malware-scanning provider remain open. Candidate document categories, candidate MFA, and post-decline/withdrawal access were subsequently approved for Phase 1C in `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`.
- Roles allowed to approve profiles, onboarding exceptions, FSRA evidence, final activation, privacy contact, and incident/security owners.
