# Plan: Minimal Agent Retrieval + Assignment Email (Scope B)

**Branch:** `feat/agent-retrieval-minimal`
**Base:** `main` at `9abb078` (post PR #19 / Phase D.2 merge)
**Worktree:** `/home/john/dev/keeper-financial-agent-retrieval`
**Approval authority:** `docs/35_AGENT_FULL_DATA_PRIVACY_APPROVAL.md` (owner-approved 2026-07-27)
**Exclusions:** full CRM, lead workflow, bulk export, marketing, independent portals/microsites,
webhooks, underwriting/lender submission, co-borrower collaboration, borrower portal.

## Goal

Let an assigned, AAL2-verified, active agent:
1. Receive a transactional email when an administrator assigns a submitted application to them.
2. Sign in (Supabase Auth, existing `agent` role + active `Candidate`).
3. Open a minimal agent surface that lists their assigned submitted applications.
4. Retrieve the **full** submitted application (unmasked SIN + assets/liabilities/subject
   property/other properties/notes) for the exact application assigned to them, plus
   decrypting document download and audited SIN access — reusing the existing authorized API.

## Scope

### A. Assignment email (new, bounded)
- New `apps/api/src/keeper_api/services/borrower_notifications.py`:
  - `send_assignment_email(agent_email, agent_name, application_id, settings)` using
    `smtplib` to `settings.smtp_host:settings.smtp_port` (local: `127.0.0.1:54324` Inbucket;
    prod: configurable). Failures are logged and MUST NOT fail the assignment transaction.
  - Single plain-text + minimal HTML message: "Application assigned; sign in to review."
    No PII beyond the agent's own name/email and the application id; no borrower PII in email.
- `Settings` additions (`core/config.py`): `smtp_host`, `smtp_port`, `smtp_from`,
  `smtp_enabled` (default false; enabled in local `.env`).
- Hook `assign_submitted_application` (`services/borrower_applications.py`) to call the
  email after a successful assignment + commit, wrapped in try/except so mail errors are
  non-fatal.
- Tests: deterministic fake SMTP (monkeypatch `smtplib.SMTP`) asserting exactly one message
  to the assigned agent's verified email, with no borrower PII; and that mail failure does
  not abort assignment.

### B. Agent full-data projection (privacy-boundary change, per docs/35)
- New schema `BorrowerAgentProjection` (in `schemas/borrower_internal.py`):
  - Same identity/address/employment as masked info but **unmasked `sin` (str)**.
  - Adds `assets`, `liabilities`, `subject_property`, `other_properties`,
    `additional_notes` from the stored payload.
  - Excludes encryption keys, capability material, raw document object keys.
- New service `get_agent_projection(db, crypto_state, application_id)` returning
  `BorrowerAgentProjection` for the exact assigned agent, raising `ValueError` when missing
  evidence (mirrors `get_internal_projection` guard logic).
- New route `GET /{application_id}/agent` (in `borrower_applications.py`) protected by
  `require_internal_agent_access`, returning `BorrowerAgentProjection`, recording an audit
  event `borrower_application_agent_viewed` with safe metadata.
- Regenerate OpenAPI + TypeScript contracts (`make openapi`).

### C. Minimal agent web surface (reuse existing API)
- Extend `requirePortalAccess` (`apps/web/lib/require-portal-access.ts`) to accept area
  `"agent"` and route to Supabase session + agent role check (no admin MFA special-case).
- Add `apps/web/app/(agent)/agent/page.tsx`: lists the agent's assigned submitted
  applications (new lightweight API `GET /api/v1/borrower-applications/agent/assigned` or
  reuse a filtered admin list scoped to the principal — must be agent-scoped server-side).
- Add `apps/web/app/(agent)/agent/[applicationId]/page.tsx`: calls the new `/agent`
  projection + existing document list/download; renders the full data read-only for
  Filogix population.
- Middleware: register the `(agent)` segment for the existing auth/role guard.
- Tests: web render test asserting an agent sees their assigned application and the full
  projection fields; an admin sees masked (no regression); a non-assigned agent is denied.

### D. Documentation
- `docs/35_AGENT_FULL_DATA_PRIVACY_APPROVAL.md` (written).
- Update `docs/00_PROJECT_SOURCE_OF_TRUTH.md` checkpoint + `docs/14_TEST_STRATEGY.md`
  (agent retrieval additions) + `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md`
  (agent view note) + `docs/11_ENVIRONMENT_VARIABLES.md` (SMTP vars).
- `docs/36_AGENT_RETRIEVAL_MINIMAL_PLAN.md` (this plan) + a completion report at the end.

## Acceptance criteria
- Assignment emails send to the assigned agent's verified address via local Inbucket;
  mail failure is non-fatal and logged.
- An assigned AAL2 active agent can sign in and retrieve full unmasked application data
  for exactly their assigned application(s); administrators still see the masked view.
- Non-assigned agents, admins-as-agent, and unauthenticated/users are denied the agent
  projection (401/403/404 as appropriate, fail closed).
- All retrievals are audited with safe metadata.
- API suite green (expected opt-in skips); web suite green; lint/typecheck/mypy/format/
  `git diff --check`/build green; one Alembic head unchanged (no schema change needed).

## Security / privacy constraints
- No new data class; projection reads the existing encrypted payload.
- Email contains no borrower PII.
- Agent full-data access is exactly-scoped to `assigned_agent_id`; no cross-application.
- Audit on every agent view + SIN access.
- SMTP credentials stay in `.env` (gitignored); never committed.

## Validation commands
- `make lint && make typecheck`
- `apps/api/.venv/bin/pytest apps/api/tests -q`
- `npm run test`
- `make openapi` then re-run web/typecheck
- `git diff --check`

## Git restrictions
- One dedicated branch/worktree (`feat/agent-retrieval-minimal`); do not touch `main`
  directly; do not alter shared DB; no destructive Git; no deploy.
- Commit only after tests green; push branch and open PR for owner merge.

## Stop conditions
- If a full CRM/portal or webhook requirement appears, stop and re-confirm scope.
- If prod SMTP behavior cannot be made configurable without secrets in repo, stop.
- Do not expand the privacy boundary beyond docs/35.
