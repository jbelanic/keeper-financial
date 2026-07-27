# Candidate Authentication and Onboarding Readiness Assessment

**Date:** 2026-07-17  
**Branch:** `chore/linux-mint-hermes-continuation`  
**Implementation checkpoint:** Phase 1D `6349c16`, Phase 1E `384246c`, ClamAV `e9d9f65`  
**Assessment mode:** Read-only implementation, contract, test, and documentation review  
**Disposition:** Phase 1C/1D completion defects confirmed at the Phase 1F readiness gate; not remediated in this documentation task

## Purpose and authority

This document is the current erratum for candidate entry, authentication/session orchestration, review lifecycle, onboarding assignment, controlled-document acknowledgement, and activation language. It does not alter the approved Phase 1C candidate policy, historical implementation reports, issued migrations, API route paths, or the approved local PostgreSQL/Supabase Auth/MinIO/ClamAV topology.

The governing rules remain:

- Supabase Auth proves identity only; local PostgreSQL relationships, roles, lifecycle, ownership, and resource rules authorize access.
- Candidate provisioning may occur only through an explicit, verified, published-posting application start.
- Generic sign-in must remain non-provisioning.
- Recruitment decisions are application-specific when a candidate has multiple applications.
- Onboarding follows conditional selection and uses an active plan.
- A controlled-document acknowledgement is authorized only for the exact version assigned to the candidate.
- Gate satisfaction and `activation_ready` are readiness evidence, not final activation.

## Assessment result

The API and web components for registration, callback exchange, narrow application start, review, onboarding, acknowledgements, and activation gates exist. The complete candidate journey is not release-ready. The review confirmed entry/recovery and session-verification gaps plus application-specific lifecycle, onboarding-assignment, navigation, and acknowledgement authorization defects.

No authentication bypass was identified. The unmapped-user denial is correct and fail-closed. The absence of a supported posting-bound existing-user recovery path is a completion/availability defect around that security boundary; it must be fixed without weakening the denial or making generic sign-in provision users.

## Exact candidate-entry breakpoint

### New-account path present in code

```text
published posting
  → /auth/register?posting={slug}
  → Supabase signUp with /auth/callback?posting={slug}
  → callback exchanges code for SSR cookie session
  → POST /api/v1/recruitment/postings/{slug}/applications/start
  → posting-specific candidate application
```

This is the only browser orchestration that reaches the narrow provisioning boundary. Its genuine local Supabase callback, cookie persistence, refresh, and cross-request lifecycle remain insufficiently verified.

### Existing confirmed but locally unmapped user

```text
published posting
  → registration action only; no posting-bound sign-in action
  → user manually discovers /auth/sign-in
  → password authentication succeeds without posting context
  → redirect to /candidate
  → /api/v1/auth/access?area=candidate denies the unmapped identity
  → redirect back to generic sign-in
```

The exact missing bridge is after posting-bound password authentication: there is no supported operation that retains the validated posting slug and invokes the existing `POST /api/v1/recruitment/postings/{slug}/applications/start` boundary. Calling that API from generic sign-in without explicit posting context would be incorrect.

## Confirmed findings and classifications

| ID           | Phase | Finding                                                                                                                                                  | Security classification                                                                                         | Current evidence                                                                                                                                                                | Remediation disposition                                                                                                                 |
| ------------ | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `ENTRY-01`   | 1C    | Published posting exposes registration only; no posting-preserving existing-user sign-in.                                                                | Release-blocking workflow completion; security-relevant because recovery must preserve explicit posting intent. | Posting detail links only to `/auth/register?posting=...`.                                                                                                                      | Add a posting-bound existing-user sign-in action and retain a validated slug through application start.                                 |
| `ENTRY-02`   | 1C    | Generic `/auth/sign-in` is not discoverable from the posting and loses posting context.                                                                  | Fail-closed availability/recovery defect; not an authorization bypass.                                          | Password sign-in allow-lists only `/candidate` or `/admin` return roots and never calls application start.                                                                      | Keep generic sign-in non-provisioning; create a distinct posting-bound orchestration.                                                   |
| `ENTRY-03`   | 1C    | `/auth/callback` is the only posting-bound local-provisioning bridge.                                                                                    | Security-sensitive single-path assurance gap.                                                                   | Callback alone exchanges the code and invokes `applications/start`.                                                                                                             | Reuse the same narrow API boundary for registration and posting-bound existing-user sign-in; test idempotency.                          |
| `ENTRY-04`   | 1C    | Confirmed, locally unmapped users are denied correctly but have no supported recovery path.                                                              | Correct fail-closed authorization plus release-blocking recovery defect.                                        | Portal access requires a mapped local principal; generic sign-in cannot create one.                                                                                             | Recover only from a published posting with explicit context; never provision from generic sign-in.                                      |
| `SESSION-01` | 1C    | SSR cookie plumbing exists, but callback persistence, refresh, expiry/revocation, and browser/server cross-request behavior are not adequately verified. | Security assurance blocker.                                                                                     | Server client reads/writes cookies; Server Components catch cookie-write failure; no genuine local callback/refresh E2E evidence was found.                                     | Add genuine local Supabase ES256 JWT/JWKS and browser cookie lifecycle tests.                                                           |
| `NAV-01`     | 1D    | Candidate onboarding route exists but is absent from candidate navigation.                                                                               | Workflow discoverability defect; direct-route authorization remains mandatory.                                  | Candidate shell links only Overview and Applications.                                                                                                                           | Expose onboarding for eligible candidates and keep server-side route checks.                                                            |
| `NAV-02`     | 1D    | Admin onboarding route exists but is absent from administration navigation.                                                                              | Operational workflow discoverability defect.                                                                    | Admin shell links do not include `/admin/onboarding`.                                                                                                                           | Expose onboarding to authorized administrators; navigation is not authorization.                                                        |
| `LIFE-01`    | 1D    | Review decisions are candidate-wide and validate an allowed target rather than an application-specific current-to-target transition.                     | Authorization and record-integrity blocker.                                                                     | Decision routes identify `candidate_id`; service changes `Candidate.status`; target allow-list does not enforce the approved transition map or isolate concurrent applications. | Introduce an approved application-specific lifecycle operation and tests; preserve other attempts.                                      |
| `ONB-01`     | 1D    | Assignment accepts any broad active-review status rather than only the intended `conditionally_selected` application.                                    | Authorization and lifecycle-integrity blocker.                                                                  | Assignment checks `REVIEW_QUEUE_STATUSES`, which includes submitted/review/interview and later onboarding states.                                                               | Require the selected application/attempt to be `conditionally_selected`.                                                                |
| `ONB-02`     | 1D    | Assignment does not reject an inactive plan.                                                                                                             | Configuration/lifecycle-integrity blocker.                                                                      | Plan lookup and assignment do not enforce `plan.is_active`.                                                                                                                     | Validate the plan is active before any supersession, task creation, or lifecycle change.                                                |
| `DOC-01`     | 1D    | Acknowledgement does not prove that the document version is assigned to the candidate.                                                                   | Resource-authorization and evidence-integrity blocker.                                                          | Route loads any existing `DocumentVersion`; service checks candidate actor only before recording acknowledgement.                                                               | Authorize the exact issued version through the candidate's active onboarding assignment and reject unassigned/cross-candidate versions. |
| `ACT-01`     | 1D    | Gate satisfaction and `activation_ready` exist; final agent activation does not.                                                                         | Claim/operation boundary.                                                                                       | No final activation API operation was identified.                                                                                                                               | Retain readiness-only language until a separately approved final activation operation exists.                                           |

## Historical-claim erratum

Historical Phase 1C and Phase 1D evidence remains unchanged because it records what was delivered and tested at those checkpoints. The current Phase 1F readiness assessment narrows the interpretation of broad completion language:

- Phase 1C registration, callback, and narrow provisioning components are implemented, but the posting-bound existing-user sign-in/recovery journey and genuine local session lifecycle are not complete.
- Identity-only denial remains correct and must not be weakened to close the journey.
- Phase 1D routes, UI pages, plan/task operations, acknowledgements, gates, and focused tests are implemented, but application-specific lifecycle enforcement, conditional-selection-only assignment, active-plan validation, assigned-version acknowledgement authorization, and onboarding navigation are completion defects.
- Phase 1D implements activation readiness only, not final activation.

This erratum supersedes any present-tense reading of the historical reports that would imply these journeys and controls are currently proven complete. It does not rewrite or invalidate evidence for the components that do exist.

## Required remediation and validation gate

Remediation requires a separately approved consolidated implementation prompt. It must preserve route compatibility unless an owner-approved API decision says otherwise, keep the application database authoritative, and add server-side authorization before UI exposure.

The gate requires:

- published-posting registration and existing-user sign-in that both preserve posting context;
- callback and password orchestration through the narrow, idempotent application-start boundary;
- genuine local Supabase JWT/JWKS and SSR cookie callback/refresh/expiry/revocation evidence;
- browser E2E through candidate application entry and eligible onboarding entry;
- candidate/admin onboarding navigation with direct-route authorization;
- application-specific lifecycle transitions and cross-application isolation;
- `conditionally_selected`-only assignment against an active plan;
- assigned-version acknowledgement authorization; and
- explicit proof that `activation_ready` does not perform final activation.

## Residual blockers outside this assessment

The known Alembic model/schema drift remains a separate Phase 1F readiness blocker. It must receive a reviewed forward migration or explicit disposition; issued migrations must not be rewritten to silence `alembic check`.

## 2026-07-17 remediation addendum

The owner approved a separate consolidated implementation prompt after this
read-only assessment. Branch `fix/candidate-auth-onboarding-completion`
remediates `ENTRY-01` through `ENTRY-04`, `NAV-01`, `NAV-02`, `LIFE-01`,
`ONB-01`, `ONB-02`, and `DOC-01` in source and focused tests. `ACT-01` remains
an intentional boundary: the implementation calculates readiness and exposes
no final activation route.

`SESSION-01` now has deterministic callback-cookie, refresh propagation,
expiry, and local ES256 verification coverage plus an opt-in genuine local
Supabase/Mailpit journey. It is fully closed as live-stack evidence only when
that opt-in journey is executed successfully on the review host; a skipped
run is reported as a residual validation blocker, not treated as a pass.

The implementation keeps the original candidate-id route families for
compatibility but requires an exact `application_id` for every review,
decision, and assignment operation. Forward migration `20260717_0006` adds
application/assignment provenance and exact assigned-document relationships;
ambiguous legacy rows are not guessed or backfilled. See
`docs/23_CANDIDATE_AUTH_ONBOARDING_COMPLETION_IMPLEMENTATION_REPORT.md` for
current evidence. The original assessment above remains unchanged historical
evidence.

## 2026-07-18 live identity-verification addendum

The opt-in local Supabase/Mailpit journey now passes for fresh synthetic
identities. Investigation of the genuine posting-bound `403` proved that the
Next.js callback and password route forwarded a current bearer correctly and
that JWT signature, issuer, audience, expiry, and route selection had already
passed. The start dependency failed because it expected top-level JWT email-
verification claims that local Supabase did not emit; no existing local
identity, role, or candidate dependency caused the denial, and no partial
application rows were created.

The corrected start boundary validates the JWT, then confirms the exact UUID
subject, signed email, and authoritative `email_confirmed_at` through local
Supabase Auth `/user` using the same bearer and browser-safe anon key. It does
not trust user-editable metadata or require local candidate rows before the
atomic transaction that creates them. Generic sign-in remains non-provisioning,
and ordinary candidate access still requires the resulting PostgreSQL mapping,
role, ownership, active state, and lifecycle. `SESSION-01` has successful local
callback/cross-request evidence; refresh-token revocation remains operational
readiness work.

## 2026-07-18 browser-completion addendum

The application-start `403` is resolved and live candidate draft save and
submission succeeded. The earlier draft `422` was not a broken save endpoint:
it reflected valid Phase 1C rules that were not discoverable without developer
tools. The completion worktree now makes those rules visible and maps safe
validation details to fields.

The shared candidate shell now uses a minimal assignment-availability response;
no assignment is stable and does not invoke the full onboarding projection on
every render. Candidate documents reuse the approved TOTP enrollment/challenge
ceremony with an exact application/document return and post-refresh AAL2 proof.
Administrator information requests require the exact selected application and
are enabled only in `under_review` or `interview`; candidate-visible request
text remains separate from internal notes. The fresh genuine candidate rerun
passed through stable pre-onboarding, draft save/submission, real TOTP AAL2, and
owned document metadata access. A fresh genuine admin-browser information
request remains pending; current evidence is recorded in `docs/23`.
