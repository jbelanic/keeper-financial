# Phase C Borrower Web Form Completion Report

- **Report date:** 2026-07-25
- **Branch:** `feat/borrower-web-form`
- **Worktree:** `/home/john/dev/keeper-financial-phase-c`
- **Base/HEAD during implementation:** `9068cdefe86105c09b2465758b62dbe71c3bf1df`
- **Alembic head:** `20260724_0011` (one head; unchanged)
- **Status:** Phase C web source implemented and deterministically validated; subject-property vocabulary reconciled (see §5). Owner acceptance and genuine-browser evidence remain pending. This is not production, pilot, deployment, or real-borrower approval.

## 1. Confirmed scope

Phase C creates a dynamic, accountless Keeper borrower experience at `/mortgage-application` and exact-host routing for `apply.localhost:3000` and `apply.keeperfinancial.ca`. The public `/apply` page now enters the Keeper-owned origin instead of calling the former integration redirect.

The client:

- starts or recovers one exact draft using the API-owned HTTP-only capability cookie;
- keeps only the opaque application ID in `sessionStorage` as a recovery locator;
- uses relative same-origin, credentialed, `no-store` start/get/patch requests with the borrower CSRF marker;
- never reads or embeds the capability;
- keeps form answers and SIN out of local/session storage, URLs, analytics, console output, server-rendered HTML, and Next cache;
- renders a saved SIN only as provided/masked state and accepts replacement without retrieval;
- advances only after a committed PATCH response and preserves visible values/step/focus context on failure;
- implements one primary and zero/one co-borrower, employment/income, assets/liabilities with completeness acknowledgements, subject/other property, mortgages, bounded notes, agent-preference provenance, and synthetic versioned privacy/credit-use consent UI;
- exposes a disabled, clearly deferred Phase D submission affordance and contains no borrower submit request.

No Supabase borrower identity, MUI, typed-name signature, marketing consent, browser payload model, Discord path, document upload, submission endpoint, Filogix/bureau/lender integration, deployment, secret, shared-database mutation, or API change was introduced.

## 2. Security and privacy evidence

- `apps/web/lib/borrower-application-api.ts` sends `credentials: "include"` and `cache: "no-store"` and adds `X-Keeper-Borrower-CSRF: 1` only for mutations.
- The raw capability is absent from TypeScript state, request construction, storage APIs, URLs, and tests.
- API-client tests use the clearly synthetic Luhn-valid SIN `046454286` only in an in-memory request assertion and prove storage/URL exclusion.
- Recovery storage contains only an opaque UUID. The redacted GET supplies revision/lifecycle plus `has_sin`/`has_co_borrower`; it never supplies a SIN or ordinary answers.
- The Next page is `force-dynamic`, has `revalidate = 0`, and opts out of indexing/caching metadata.
- Exact application-host handling returns before Supabase client construction. Conflicting `X-Forwarded-Host` and `Host` values fail with `400`.
- Network/503 and stale/validation paths do not advance, clear, or falsely confirm a save.
- No API, migration, generated contract, dependency manifest, lockfile, MinIO, ClamAV, Supabase, secret, or external service was changed.

## 3. Accessibility evidence

Deterministic tests cover native keyboard-operable inputs/buttons, explicit labels, one co-borrower boundary, stable repeat-entry keys and indexed accessible names, focus transfer to an announced error summary, focus to the next section only after save success, polite save status, text plus colour status, and a disabled submission control with explanatory text.

Responsive CSS uses `minmax(0, 1fr)`, wraps action/progress controls, collapses the two-column form at 36 rem, avoids sticky noninteractive progress content, and preserves global visible focus/reduced-motion controls.

No Chromium/Playwright executable is installed in this environment. Attempting to bind the built Next server to port 3000 failed with sandbox `listen EPERM`. Therefore no genuine-browser keyboard, zoom, screen-reader, network-panel, or measured 320 CSS-pixel evidence is claimed. Those remain required before owner acceptance/real-data operation.

## 4. Validation results

| Command | Result |
| --- | --- |
| `npm run test` | PASS — web 170 passed, 3 opt-in integration skips; contracts/UI have no test scripts |
| `npm run lint` | PASS — web and UI ESLint |
| `npm run typecheck` | PASS — web, contracts, and UI TypeScript |
| `npm run format:check` | PASS — web, contracts, and UI Prettier |
| `npm run build` | PASS after replacing a validation-only out-of-worktree `node_modules` symlink with an exact-lock local dependency tree; 34 routes generated and `/mortgage-application` is dynamic |
| `npm run audit:ci` | ENVIRONMENT-BLOCKED — policy wrapper could not spawn nested `npm audit` (`spawnSync npm EPERM`) |
| `npm audit --json` | ENVIRONMENT-BLOCKED — registry DNS/network unavailable (`ENOTFOUND registry.npmjs.org`) |
| `make test` | PASS — repeats web 170 passed/3 skipped, then API 504 passed/11 skipped/8 warnings |
| `make lint` | PASS — ESLint and Ruff (`All checks passed!`) |
| `make typecheck` | PASS — TypeScript and mypy (`Success: no issues found in 63 source files`) |
| `../../.venv/bin/alembic heads` from `apps/api` | PASS — one head, `20260724_0011` |
| `git diff --check` | PASS |

The first exact `npm run build` attempt failed before compilation because Turbopack rejects an external `node_modules` symlink. The exact lockfile hash matched the dependency source; copying that installed tree locally made the unchanged build pass. `npm ci` could not construct it directly because the sandbox denied esbuild's install-time binary check (`EPERM`).

## 5. Subject-property API contract — current state

On branch `feat/borrower-web-form`, the borrower-application draft API and web subject-property handling are reconciled as follows:

- **Partial PATCH merge:** `save_draft_payload()` in `apps/api/src/keeper_api/services/borrower_applications.py` decrypts the prior revision and deep-merges the incoming section via `_deep_merge`, so incremental section saves accumulate rather than replace. This behavior is committed at `5a9912b` and is unchanged by the vocabulary fix below.
- **Subject-property schema:** `SubjectProperty` in `apps/api/src/keeper_api/schemas/borrower_payload.py` defines `property_type`, `property_style`, `occupancy`, `lot_details`, `garage_details`, and related fields, all under `extra="forbid"` (fail-closed). The permissive draft model `BorrowerApplicationDraftInput` validates partial section saves; `validate_borrower_draft()` is the entry point used by the PATCH route.
- **Web/API vocabulary alignment (resolved):** the subject-property section previously emitted `occupancy` values `rental`/`second_home` and a free-text `property_style`, which would return `422` against the API enum. Under owner decision A — the web follows the existing API enum, with no API/schema/enum change — the occupancy `<select>` now emits exactly `owner_occupied`, `tenant`, `vacant`, `other`, and `property_style` is a closed `<select>` over `detached`, `semi_detached`, `townhouse_row`, `apartment`, `other`. No `second_home` or `rental` value was added; no API change was made. This reconciliation landed in commit `322e359`.

Result: a backend-backed partial PATCH carrying a subject-property section now validates against the existing API schema for in-vocabulary values. Validation on this machine (web 171 passed / 3 skipped after the added vocabulary test; API suite green on in-memory SQLite; one Alembic head `20260724_0011`) confirms the web emits only in-vocabulary values. A real PostgreSQL-backed PATCH run and genuine-browser evidence remain deferred (see §7).

## 6. Files changed

Created:

- borrower layout, page, form, and bounded components under `apps/web/app/(borrower)/mortgage-application/`;
- `apps/web/lib/borrower-application-api.ts`;
- `apps/web/tests/borrower-application.test.tsx`;
- `apps/web/tests/borrower-application-api.test.ts`;
- this report.

Modified:

- `apps/web/proxy.ts`;
- `apps/web/lib/routes.ts`;
- `apps/web/lib/site-config.ts`;
- `apps/web/app/(public)/apply/page.tsx`;
- `apps/web/app/globals.css`;
- affected web route/config/proxy/apply tests;
- living architecture, requirements, API/data, test-strategy, and limitations documents.

No API, contract, migration, dependency, lockfile, historical report, external system, or operational configuration file changed.

## 7. Deferred scope and release risks

1. (Resolved) The partial PATCH/merge and subject-property vocabulary discrepancy was reconciled under owner decision A — web follows the existing API enum, no API change (see §5). A real PostgreSQL-backed PATCH run remains deferred for full parity evidence.
2. Phase D owns documents, immutable submission snapshot, exact approved consent enforcement, capability revocation, and the real submit operation.
3. Exact production consent wording/version is still unapproved; this UI uses conspicuously synthetic draft wording.
4. Genuine browser/accessibility, exact cookie behavior, ingress/TLS, abuse controls, key custody, backup/restore, retention/purge/legal hold, monitoring, incident response, and deployment evidence remain required.
5. Both borrower feature gates/configuration wiring remain unavailable for real operation.
6. The advisory result could not be refreshed in the network-restricted sandbox; the repository policy was not weakened.

Passing source tests is necessary but not sufficient for accepting real borrower-data operation.

## 8. Git operation and exact status

The implementation remains uncommitted because the managed worktree exposes Git metadata read-only. The bounded `git add` attempt failed before staging with:

`Unable to create .../.git/worktrees/keeper-financial-phase-c/index.lock: Read-only file system`

No commit, push, pull request, merge, force-push, history rewrite, branch deletion, deployment, or external operation was performed.

Exact `git status --short` after source completion:

```text
 M apps/web/app/(public)/apply/page.tsx
 M apps/web/app/globals.css
 M apps/web/lib/routes.ts
 M apps/web/lib/site-config.ts
 M apps/web/proxy.ts
 M apps/web/tests/apply-page.test.tsx
 M apps/web/tests/public-config.test.ts
 M apps/web/tests/routes.test.ts
 M apps/web/tests/supabase-session-refresh.test.ts
 M docs/03_ARCHITECTURE_BASELINE.md
 M docs/13_API_AND_DATA_INVENTORY.md
 M docs/14_TEST_STRATEGY.md
 M docs/15_KNOWN_LIMITATIONS.md
 M docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md
?? apps/web/app/(borrower)/
?? apps/web/lib/borrower-application-api.ts
?? apps/web/tests/borrower-application-api.test.ts
?? apps/web/tests/borrower-application.test.tsx
?? codex-phase-c-run2.log
?? codex-phase-c.log
?? docs/31_PHASE_C_BORROWER_WEB_FORM_COMPLETION_REPORT.md
```

The two `codex-phase-c*.log` paths predated this implementation run and were not opened, modified, staged, or deleted.
