# Linux Mint Continuation Readiness Report

**Date:** 2026-07-17  
**Branch:** `chore/linux-mint-hermes-continuation`  
**Base checkpoint:** `e9d9f6535244cd93eeee3e27d2b72d5ff89e14aa`  
**Status:** Linux Mint reconstruction is operational and the reconciled continuation baseline is ready to commit. Candidate-readiness defects and Alembic drift remain classified Phase 1F blockers; this is not pilot or launch approval.

## Approved checkpoint

| Checkpoint                                                     | Commit                                     | Status   |
| -------------------------------------------------------------- | ------------------------------------------ | -------- |
| Phase 1D candidate review and onboarding                       | `6349c16c715430bc98c6cc1bca212a8cc55e9def` | Complete |
| Phase 1E agent profiles and approved local deployment topology | `384246ceb4f667f422fb82271e1145b79aea67a6` | Complete |
| Approved local ClamAV malware scanning                         | `e9d9f6535244cd93eeee3e27d2b72d5ff89e14aa` | Complete |

Phase 1F readiness planning and blocker resolution is the next gate. Phase 1D and Phase 1E are not pending implementation phases.

## Linux Mint reconstruction status

The application was reconstructed and operated successfully on Linux Mint at the approved checkpoint.

The approved local-container topology is:

- application PostgreSQL for application and authorization data;
- FastAPI API;
- Next.js frontend;
- local Supabase Auth for identity semantics;
- Mailpit for local Auth email capture;
- private MinIO for application object bytes;
- fail-closed ClamAV scanning before supported document persistence.

Supabase Studio is permitted only as local operator tooling. Supabase Storage and its S3 protocol remain disabled and are not application storage.

This proves local operability. It is not a backup/restore drill, disaster-recovery proof, host-hardening approval, accessibility certification, legal/privacy approval, pilot approval, or launch authorization.

## Service and infrastructure verification

### Docker Compose configuration

`docker compose config --quiet` completed successfully.

### Running infrastructure

`docker compose ps --all` confirmed:

| Service              | Result                                               |
| -------------------- | ---------------------------------------------------- |
| PostgreSQL `db`      | Running and healthy; loopback `127.0.0.1:5432`.      |
| MinIO                | Running and healthy; loopback `127.0.0.1:9000-9001`. |
| MinIO initialization | Exited successfully with status `0`.                 |
| ClamAV               | Running and healthy; loopback `127.0.0.1:3310`.      |

The API and frontend were not running as Compose services during the first health probe. This was an execution-state issue, not evidence of an application failure.

### API health

The first `curl http://localhost:8000/health` failed because the API process was not running.

After `make api-dev`:

- `/health` returned HTTP `200`;
- `/health/db` returned HTTP `200`;
- API startup and shutdown completed normally.

## Database and migration validation

### Migration execution

`make migrate` completed successfully.

### Current migration head

`docker compose run --rm api alembic current --check-heads` returned:

```text
20260717_0005 (head)
```

### Alembic metadata/schema drift

`docker compose run --rm api alembic check` remains non-green.

Detected differences include:

- missing model-declared indexes on:
  - `candidate_esign_envelopes.candidate_id`;
  - `candidate_information_requests.candidate_id`;
- model/migration index differences for:
  - `candidate_onboarding_assignments`;
  - `programmatic_gates`;
- foreign-key `ondelete` differences for:
  - `candidate_onboarding_tasks.onboarding_task_id`;
  - `candidate_onboarding_tasks.reviewed_by_user_id`;
  - `policy_acknowledgements.document_version_id`.

This is a Phase 1F blocker. It requires a focused model-versus-issued-migration investigation and a reviewed forward correction or explicit disposition. Issued migrations must not be rewritten merely to make the diagnostic green.

## Code-quality and test validation

### Lint

The approved import-order correction was applied in `apps/api/tests/test_sensitive_upload_middleware.py`.

```text
make lint
All checks passed!
```

ESLint completed with zero warnings for the web and UI workspaces, and Ruff passed for `apps/api`.

### Type checking

`make typecheck` passed:

- frontend/workspace TypeScript checks passed;
- MyPy passed with no issues in 55 API source files.

### Automated tests

Frontend tests passed:

```text
21 test files passed
77 tests passed
```

API tests produced:

```text
281 passed
1 skipped
3 warnings
```

The approved configuration correction now permits Studio only with the tracked local operator settings and continues to assert that Supabase Storage, its S3 protocol, storage analytics, and storage vector services are disabled.

### Build

`make build` passed.

The Next.js route inventory includes:

- `/auth/register`;
- `/auth/sign-in`;
- `/auth/callback`;
- `/candidate`;
- `/candidate/application`;
- `/candidate/applications/[applicationId]`;
- `/candidate/documents`;
- `/candidate/onboarding`;
- corresponding admin and public routes.

The presence of these routes does not by itself prove the complete candidate login, provisioning, authorization, navigation, and onboarding-entry journey.

### Generated contracts

`make openapi` completed successfully twice.

Both runs produced identical hashes and no generated-contract diff:

```text
b1c262b6e3136a4688c3a26d8b4c63fd80c3a0d4cfdad6984d15bada81afb374  packages/contracts/openapi.json
dba8994ba64999748b9b7062ebc1a43086a254ad79edd0dd1273df61d8e19760  packages/contracts/src/generated.ts
```

### Diff validation

`git diff --check` passed.

## Phase 1D and Phase 1E route verification

The Phase 1D and Phase 1E methods and paths documented in `docs/13_API_AND_DATA_INVENTORY.md` match the generated OpenAPI contract.

Verified Phase 1D route groups include:

- admin candidate queue/detail;
- interview;
- information requests;
- administrative decisions;
- onboarding assignment;
- onboarding plans;
- candidate task review;
- external e-signature envelope references;
- activation-gate satisfaction;
- controlled-document listing;
- candidate onboarding dashboard;
- candidate task evidence;
- exact-version acknowledgements.

Verified Phase 1E route groups include:

- public agent directory/detail;
- admin profile list/create/get/update;
- profile approval/publication/suspension/archive lifecycle.

The implemented onboarding contract exposes activation-gate satisfaction and an `activation_ready` calculation. No final candidate-to-active-agent activation operation was identified. Documentation must describe readiness and gate satisfaction, not completed final activation.

## Candidate authentication and onboarding readiness assessment

Manual local verification previously confirmed:

- a visitor can create a Supabase account;
- Mailpit receives the confirmation message;
- the account can be confirmed;
- the confirmed user appears in Supabase Studio Authentication.

The focused read-only assessment confirmed that the complete browser journey is not merely unverified; it contains Phase 1C/1D completion defects. Detailed evidence and the current historical-claim erratum are in `docs/22_CANDIDATE_AUTH_AND_ONBOARDING_READINESS_ASSESSMENT.md`.

### Exact breakpoint

For a new registration, the designed path retains the posting slug through `/auth/register` and `/auth/callback`, exchanges the Supabase code for a cookie session, and invokes the narrow posting-specific application-start API. Genuine local callback, refresh, and cross-request persistence still require browser E2E proof.

For an existing confirmed but locally unmapped user, the exact break occurs before local provisioning:

1. the published posting exposes registration only;
2. `/auth/sign-in` is not discoverable from the posting and receives no posting slug;
3. password authentication can succeed and redirect to `/candidate`;
4. `/api/v1/auth/access?area=candidate` correctly denies the unmapped identity; and
5. no supported posting-bound path invokes `POST /api/v1/recruitment/postings/{slug}/applications/start` for that existing user.

Generic sign-in must remain non-provisioning. Recovery must start from an explicit published posting, preserve its validated slug, and reuse the existing narrow application-start boundary.

### Confirmed completion defects

- posting-bound registration lacks a parallel posting-bound existing-user sign-in/recovery action;
- callback/session cookie persistence and refresh/expiry/revocation behavior lack genuine local Supabase E2E evidence;
- candidate and admin onboarding routes are absent from their respective navigation;
- review decisions are candidate-wide rather than application-specific and do not enforce current-to-target lifecycle maps;
- onboarding assignment does not require the intended application to be `conditionally_selected` and does not require an active plan;
- controlled-document acknowledgement does not prove the exact version is assigned to the candidate; and
- only activation-gate satisfaction and `activation_ready` exist; final activation is not implemented.

### Security classification

No authentication bypass was identified. Unmapped-user denial is correct and fail-closed. The missing existing-user recovery and navigation paths are release-blocking workflow defects around that boundary. Session lifecycle is a security-assurance blocker. Candidate-wide lifecycle changes, broad/inactive-plan assignment, and unassigned-version acknowledgement are server-side authorization and record-integrity blockers. Activation wording is a claim/operation boundary.

### Remediation disposition

This continuation task documents but does not fix the defects. They are Phase 1C/1D completion defects discovered at the Phase 1F readiness gate and require a separately approved consolidated implementation prompt plus the acceptance/test coverage in `docs/08_ACCEPTANCE_TESTS.md` and `docs/14_TEST_STRATEGY.md`. Historical Phase 1C and Phase 1D reports remain unchanged.

The required future browser journey includes:

1. finding and using the sign-in entry point;
2. establishing and persisting the Supabase browser/server session;
3. linking or provisioning the verified identity into local `User` and `UserIdentity` records;
4. obtaining the candidate role and required candidate/application relationships;
5. resolving `/api/v1/auth/access?area=candidate`;
6. reaching the candidate application workspace;
7. reaching `/candidate/onboarding` after an eligible administrative decision and onboarding-plan assignment.

A Supabase identity alone intentionally does not grant local application access. The documented breakpoint must be remediated and the full journey validated before candidate onboarding can be considered end-to-end complete.

Status: assessment complete; remediation remains required before pilot or launch approval.

## Local Supabase decisions

- Supabase Studio may be enabled only for local operator use.
- Supabase Studio is not public, shared, or an application dependency.
- Supabase Storage remains disabled.
- The Supabase S3 protocol remains disabled.
- MinIO remains the only approved application object store.
- Supabase Auth proves identity only; PostgreSQL roles, relationships, lifecycle, ownership, and resource rules authorize access.

## Current Git state

At the end of validation, the worktree contains the understood continuation delta. `apps/web/next-env.d.ts` is the pre-existing generated development-route declaration and was restored after `next build` normalized it; it is not a candidate implementation change.

```text
 M apps/api/tests/test_compose_config.py
 M apps/api/tests/test_sensitive_upload_middleware.py
 M apps/web/next-env.d.ts
 M docs/06_UX_UI_IMPLEMENTATION_GUIDE.md
 M docs/07_DELIVERY_PLAN.md
 M docs/08_ACCEPTANCE_TESTS.md
 M docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md
 M docs/10_CODEX_WORKING_AGREEMENT.md
 M docs/12_THREAT_MODEL.md
 M docs/13_API_AND_DATA_INVENTORY.md
 M docs/14_TEST_STRATEGY.md
 M docs/15_KNOWN_LIMITATIONS.md
 M docs/LOCAL_DEVELOPMENT.md
 M supabase/config.toml
?? AGENTS.md
?? docs/21_LINUX_MINT_CONTINUATION_READINESS_REPORT.md
?? docs/22_CANDIDATE_AUTH_AND_ONBOARDING_READINESS_ASSESSMENT.md
```

This is an intentional continuation delta, not a clean worktree. The validation corrections and documentation reconciliation are ready for owner review and commit as the continuation baseline. The documented Phase 1F blockers remain unresolved.

## Continuation-baseline disposition

Completed for this baseline:

- corrected and validated Ruff import ordering;
- reconciled and validated the local-only Studio expectation while keeping Supabase Storage/S3 disabled;
- completed and documented the focused candidate authentication/provisioning/onboarding assessment without implementation changes;
- ran `make lint`, `make typecheck`, `make test`, `make build`, and `make openapi` twice successfully; and
- passed `git diff --check`.

Remaining after the baseline commit:

- remediate the candidate Phase 1C/1D completion defects through a separately approved consolidated prompt; and
- resolve or explicitly disposition the known Alembic drift with no rewrite of issued migrations.

## Continuation decision

**Linux Mint environment reconstruction:** operational.

**Documentation/configuration continuation baseline:** ready to commit.

**Phase 1F implementation:** do not begin yet.

The next safe work is:

1. review and commit this continuation baseline;
2. approve a consolidated prompt for the documented candidate sign-in/provisioning/onboarding remediation;
3. investigate and disposition the Alembic drift;
4. approve the remaining Phase 1F scope; and
5. only then begin bounded Phase 1F implementation.

## 2026-07-17 candidate-completion addendum

The owner subsequently approved the consolidated candidate authentication and
onboarding completion prompt on branch
`fix/candidate-auth-onboarding-completion`. That bounded remediation now:

- provides published-posting registration and existing-user sign-in while
  retaining only a server-validated posting slug;
- preserves generic sign-in as a non-provisioning path and reuses the existing
  application-start API as the sole candidate self-provisioning boundary;
- refreshes and propagates Supabase SSR cookies on protected/auth requests;
- exposes authorized candidate/admin onboarding navigation;
- makes review transitions and onboarding assignment application-specific;
- requires `conditionally_selected` plus an active plan; and
- binds controlled-document acknowledgement and readiness to exact assignment
  versions.

Forward migration `20260717_0006` is limited to the provenance needed for
these controls. It does not resolve or claim to resolve the known general
Phase 1D Alembic drift. Historical validation and Git-state sections above
remain evidence of the continuation baseline at that time, not the current
remediation worktree. Current command evidence and residual blockers are in
`docs/23_CANDIDATE_AUTH_ONBOARDING_COMPLETION_IMPLEMENTATION_REPORT.md`.

Final activation remains unimplemented.

### Local administrator access addendum

A genuine local browser investigation subsequently confirmed that the seeded
`admin@example.test` application fixture retained placeholder Supabase subject
`00000000-0000-4000-8000-000000000002`, while the separately created local
Auth user had a different UUID. The API correctly denied that unmatched
identity. This was not an MFA or role-check bypass defect.

The remediation worktree now adds an explicit local-only, transactional
placeholder replacement command and a browser TOTP enrollment/challenge route.
The command requires an existing active `brokerage_admin`, creates no Auth user
or role, uses no service-role credential, and refuses genuine-subject or
cross-user replacement. `/auth/sign-in?returnTo=/admin` remains generic and
non-provisioning; PostgreSQL role mapping and AAL2 remain authoritative. The
subsequent genuine local ceremony successfully linked the placeholder,
enrolled TOTP, established AAL2, and reached `/admin`, `/admin/candidates`, and
`/admin/onboarding`; current evidence is recorded in `docs/23`.

### 2026-07-18 browser-completion addendum

The remaining focused pass replaces the shared shell's full onboarding
dashboard fetch with a bounded availability projection, maps no assignment to
a stable candidate state, exposes Phase 1C form requirements and safe linked
`422` errors, reuses the approved TOTP ceremony for candidate document step-up,
and keeps administrator information requests bound to the exact selected
application. The separate general Alembic drift and final activation remain
outside this work. A later stabilization rerun passed three fresh closed-tab
candidate sign-ins without focus/visibility/resize assistance, in-place draft
feedback, nonobstructing section flow, real candidate AAL2, clean ClamAV/MinIO
upload with refreshed metadata, and responsive Firefox checks at all required
320–1920 CSS-pixel widths. A fresh genuine admin-browser information request
remains pending before commit readiness. Any earlier “ready to commit” wording
in this historical continuation report refers only to its bounded baseline at
that time, not the current uncommitted remediation worktree.
