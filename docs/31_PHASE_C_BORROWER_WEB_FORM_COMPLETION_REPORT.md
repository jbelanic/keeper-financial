# Phase C Borrower Web Form Completion Report

- **Report date:** 2026-07-25
- **Branch:** `feat/borrower-web-form`
- **Worktree:** `/home/john/dev/keeper-financial-phase-c`
- **Base/HEAD during implementation:** `9068cdefe86105c09b2465758b62dbe71c3bf1df`
- **Alembic head:** `20260724_0011` (one head; unchanged)
- **Status:** Phase C web source implemented and deterministically validated; owner acceptance, genuine-browser evidence, and the API integration discrepancy below remain pending. This is not production, pilot, deployment, or real-borrower approval.

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

## 5. True API integration discrepancy

The owner clarification directed Phase C to implement the web against a permissive partial-save contract and not change the API. The generated request contract is permissive (`payload: Record<string, unknown>`), so the web sends a section-shaped partial payload and advances only on a successful PATCH.

Current runtime source differs from that stated contract:

1. `save_application()` calls `validate_borrower_payload(body.payload)`.
2. `BorrowerApplicationPayloadInput` requires `mortgage_request` and `primary_borrower`, while `BorrowerInfo` requires at least one employment entry.
3. `save_draft_payload()` encrypts the passed payload as the new revision; it does not explicitly merge a section into the prior decrypted payload.
4. Approved subject-property style, occupancy, lot, and garage fields are not present in the Phase B Pydantic schema.

Consequently, a real backend-backed first-section PATCH is expected to return `422`, and section-shaped later writes cannot safely be claimed to preserve prior sections. Phase C did not modify the API, weaken validation, or fake an integration success. The web implements the documented contract and fails safely; reconciliation requires separately authorized API work.

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

1. Reconcile the partial PATCH/merge and subject-property contract discrepancy under explicit API authority before claiming a backend-complete Phase C journey.
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
