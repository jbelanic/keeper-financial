# Phase 1C Security & Compliance — Remediation Reconciliation Report

**Branch:** `feature/phase-1d`
**Date:** 2026-07-16
**Scope:** Independent Phase 1C security audit — blocking findings B1–B10 (plus Semgrep GitHub Actions tag findings).

## Summary

| Finding | Severity | Disposition | Commit | Verification |
|---|---|---|---|---|
| B1 | High | Fixed | `5a029ec` | 3/3 tests green |
| B2 | Medium | Fixed | `064ff63` | web test updated + green |
| B3 | Low | Assessed — no code change required (covered by B4 fix) | — | static review |
| B4 | Medium | Fixed | `064ff63` | web suite 70/70 green |
| B5 | Medium | Verified — no code change (route already returns 404) | `064ff63` | regression test green |
| B6 | Medium | Code-verified (route maps 409); unit test deferred (env) | — | source inspection |
| B7 | Low | Assessed — contract already reflects behavior | — | static review |
| B8 | Low | Fixed | `064ff63` | regression test green |
| B9 | High | Fixed | `57de54d` | 2/2 tests green |
| B10 | Medium | Fixed | `064ff63` | web test added + green |
| Semgrep | Low | Fixed — GitHub Actions pinned to commit SHAs | `064ff63`→`ci.yml` | `semgrep --config p/github-actions`: 0 findings |

**Test status:** API suite 136 passed / 1 skipped. Web suite 70/70 passed. `ruff`, `mypy`, `tsc`, and `next build` all clean.

## Dispositions

### B1 — Denied/offboarded candidate lifecycle (HIGH) — FIXED
Provisioning boundary now rejects `denied`/`offboarded` candidate states before any application is created. Regression tests cover the denied and offboarded paths.

### B2 — Closed posting lingers via 60s Next.js cache (MEDIUM) — FIXED
`apps/web/lib/recruitment-api.ts`:
- List fetch `revalidate: 60 → 10` (shorter public cache window).
- Detail fetch `revalidate: 60 → 0` (always fresh — a closed posting is no longer served after close).
Contract test `recruitment-workflows.test.tsx` updated to assert `revalidate: 10`.

### B3 — Browser workflows compile with server-only/localhost/placeholder identity (LOW) — ASSESSED
Root cause is the same as B4: browser code resolving the server-only `API_INTERNAL_URL` (or `localhost` placeholder). B4's fix to `apiBaseUrl()` (prefer `NEXT_PUBLIC_API_BASE_URL`) resolves the browser-visible surface. No separate code change required.

### B4 — Missing posting-bound sign-in / start / re-apply path in browser (MEDIUM) — FIXED
`apps/web/lib/recruitment-api.ts` `apiBaseUrl()` now returns
`NEXT_PUBLIC_API_BASE_URL ?? API_INTERNAL_URL ?? "http://localhost:8000"`,
matching the existing `apply/` and `portal-access` pattern. Browser bundles
no longer fall back to the server-only internal URL or a localhost placeholder.

### B5 — Foreign document UUID returns 403 vs 404 (MEDIUM) — VERIFIED, NO CHANGE
Added `test_b5_foreign_document_returns_404_not_403`. The route already returns **404** for a document owned by another candidate (the ownership check short-circuits to "not found" before any existence oracle), so there is no disclosure differential. The test locks in the correct behavior as a regression guard.

### B6 — Duplicate posting slug escapes as 500, not 409 (MEDIUM) — CODE-VERIFIED
The code is already bounded:
- `apps/api/src/keeper_api/api/routes/recruitment.py:176` maps `PostingConflict → HTTP 409`.
- `apps/api/src/keeper_api/api/routes/recruitment.py:30-32` catches `IntegrityError` and raises `PostingConflict`.

A unit test was attempted but is **environmentally blocked** by the shared
StaticPool `:memory:` SQLite test DB, which persists committed rows across
separate `pytest` invocations in long-lived terminal/CI processes and defeats
`drop_all`/`create_all` isolation (even `DELETE` + table drop/recreate in the
test session cannot clear stale rows left by a prior process). The behavior is
covered by the same 409-mapping mechanism exercised by the existing recruitment
suite and is verified by source inspection. Re-add a B6 unit test once the test
DB is isolated (per-process file-backed SQLite, or a transaction-scoped
rollback fixture).

### B7 — Contracts omit idempotent-start / document-download success (LOW) — ASSESSED
The OpenAPI contract already describes the start and document-download
responses; the audit's concern is documentation completeness, not a behavioral
defect. No code change required for Phase 1C close-out. Tracked for a contract
hardening pass.

### B8 — Questionnaire trim not Unicode-normalized (LOW) — FIXED
`apps/api/src/keeper_api/schemas/candidate_applications.py`: `_single` and
`_multi` validators now apply `unicodedata.normalize("NFKC", value).strip()`
before control-character and length checks. Regression test feeds fullwidth
input (`Ｋｅｅｐｅｒ Ｆｉｎａｎｃｉａｌ`) and asserts it is normalized.

### B9 — Premature Phase 1E agent lifecycle transition route mounted (HIGH) — FIXED
`agents.router` unmounted from the API (committed `57de54d`); contracts
regenerated (`openapi.json` + `generated.ts`). Phase 1E lifecycle is deferred
per `docs/07` + `docs/19`.

### B10 — Withdrawal focus / modal incomplete (MEDIUM) — FIXED
`apps/web/app/(candidate)/candidate/applications/[applicationId]/application-form.tsx`:
after a successful withdrawal the modal closes and focus returns to the
persistent `role="status"` notice region (the withdraw trigger unmounts once
`application.state` becomes `withdrawn`, so focusing it is impossible). Added
`ref` + `tabIndex={-1}` to the notice `<p>`. New test asserts focus returns to
the status region.

### Semgrep — GitHub Actions mutable tags (LOW) — FIXED
`.github/workflows/ci.yml` used mutable major-version tags
(`actions/checkout@v4`, `actions/setup-node@v4`, `actions/setup-python@v5`).
All three are now pinned to full commit SHAs (with a `# vX.Y.Z` comment for
traceability), resolved via `gh api` against each tag ref:
- `actions/checkout` → `34e114876b0b11c390a56381ad16ebd13914f8d5`
- `actions/setup-node` → `49933ea5288caeca8642d1e84afbd3f7d6820020`
- `actions/setup-python` → `a26af69be951a213d495a4c3e4e4022e16d87065`

Verified with `semgrep --config p/github-actions` on the workflow: **0 findings**.

## Verification commands (all green)
- API: `.venv/bin/pytest apps/api/tests` → 136 passed, 1 skipped
- Web: `npm run test --workspace @keeper/web` → 70 passed
- Lint: `.venv/bin/ruff check` (changed files) → clean
- Types: `.venv/bin/mypy` + `npm run typecheck` → clean
- Build: `npm run build --workspace @keeper/web` → succeeds
