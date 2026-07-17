# Acceptance Tests

## Public and SEO

- Public pages render without authentication.
- Public pages have unique titles and descriptions.
- Sitemap excludes private routes.
- Robots excludes candidate, admin, and authentication areas.
- Public header and footer contain the approved navigation destinations.
- Canonical and Open Graph metadata use validated site configuration.
- Owner-supplied public name, regulatory text, address, email, phone, and application destination match controlled configuration.
- Missing optional booking/principal-broker values remain disabled or absent rather than becoming claims.
- Draft/suspended/archived agent profiles return non-public behavior.
- Closed recruitment postings are not listed publicly.
- Mobile layout remains usable at 320 CSS pixels.
- Public navigation uses keyboard-native controls and all public actions remain real links or native controls.
- Mockup-only people, ratings, lender counts, rates, licence examples, testimonials, and portal metrics do not appear in public source.

Phase 1A public-site evidence remains in `docs/17_PHASE_1A_IMPLEMENTATION_REPORT.md`. Phase 1B adds focused apply-form, attribution, booking, protected lead-queue, no-store request, consent-state, pagination, withdrawal-confirmation, and route-protection coverage.

## Apply flow

- `/apply` shows both paths.
- Contact-first form submits approved minimal fields.
- Consent wording/privacy versions and source/capture source are selected only by the server; caller override fields are rejected as extras.
- Required service-contact acknowledgement is enforced.
- Marketing consent remains optional and unchecked by default.
- A marketing-consent record is created only when selected.
- Prominent and adjacent free-text warnings cover financial, identity, health, credential, and underwriting information.
- Overly long, sensitive, control-character, unknown, and automation-trap input is rejected.
- Valid query attribution becomes a hidden controlled slug; invalid attribution is omitted and unpublished/unknown profiles are rejected by the API.
- Pending submission disables duplicates; errors preserve values, focus an announced summary, and map `422`, `429`/`Retry-After`, `503`, server, and network failures without exposing internals.
- Success is announced and is the only state that resets the form.
- Full application redirects only to configured HTTPS allowed hosts.
- Agent redirect attribution uses only safe grammar and an approved configuration mapping.
- No sensitive information appears in redirect URL.
- Phone remains a real `tel:` action; book-a-call renders only for a validated optional HTTPS URL.

## Lead administration

- `GET /api/v1/leads` and marketing withdrawal deny anonymous, unmapped identity, mapped identity-only, inactive, wrong-role, candidate, and admin-without-required-MFA callers; an active verified AAL2 admin is allowed.
- The list is no-store, maximum 100 rows per request, offset-paginated, newest-first by `created_at` then `id`, and accepts only lifecycle status filtering.
- Queue URLs contain only safe page/status values; list output contains the necessary lead fields and explicit service/marketing consent states and timestamps.
- Withdrawal affects only the lead’s marketing consent, preserves `granted_at`, sets `withdrawn_at` once, is idempotent, and never changes service acknowledgement.
- First withdrawal creates exactly one `marketing_consent.withdrawn` audit with actor, request ID, target consent ID, and safe capture source. Unknown lead or absent marketing consent returns a safe `404`.
- Lead, service consent, optional marketing consent, and audits roll back together on persistence failure.
- Request logs and audit metadata exclude contact fields, message, tokens, raw payloads, and private URL/query values.

## Authentication and authorization

- Anonymous user cannot access candidate or admin routes.
- Authenticated identity without local application access is denied.
- Every published posting exposes both registration and existing-user sign-in, and each path preserves the validated posting slug through authentication to the posting-specific application-start operation.
- Registration confirmation exchanges the callback code for a genuine Supabase session, persists the server/browser cookie session, invokes the narrow posting-bound provisioning operation exactly once, and enters the resulting application.
- Posting-bound password sign-in authenticates the existing Supabase identity, then invokes the same narrow application-start operation for the preserved published posting; retries are idempotent and do not duplicate the local user, role, candidate, or application attempt.
- Generic sign-in remains non-provisioning: without a posting context, a confirmed but locally unmapped identity is denied candidate access and receives no local user, role, candidate, or application relationship.
- A confirmed but locally unmapped existing user can recover only by returning to a published posting and using its posting-bound sign-in path; closed, archived, unknown, or malformed posting context fails closed without provisioning.
- Session cookies survive the callback and subsequent server/browser requests; valid refresh rotates cookies without losing authorization, while expired, revoked, or invalid sessions return to sign-in without leaking tokens or granting access.
- Candidate can access only own record and documents.
- Candidate cannot access internal notes.
- Candidate cannot access another candidate by changing an identifier.
- Admin action requires correct role.
- Suspended/offboarded account is denied.
- Role revocation takes effect.

## Candidate application

- Candidate saves draft.
- Questionnaire sections, fields, formats, lengths, repeat limits, optionality, prose allow-list, and server-owned fields exactly match `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`.
- Required Opportunity, Contact information, Application details, and Privacy and declaration sections prevent submission when incomplete; Employment history, Education and training, and documents remain optional.
- Submission creates status history and audit event.
- Submission records the immutable `candidate-privacy-disclosure-2026-07-15-v1` version and acknowledgement time; caller overrides fail.
- Submitted application cannot be silently edited; only the approved draft fields are candidate-editable before submission.
- Phase 1D provides an authorized admin information-request record and lifecycle transition. Submitted questionnaire revisions remain immutable; no endpoint silently overwrites or reopens a submitted questionnaire.
- Withdrawal follows valid transition policy.
- Multiple concurrent posting-specific applications are allowed, with no more than one nonterminal attempt per candidate/posting.
- Reapplication creates a new attempt and preserves the withdrawn/declined attempt, revision history, and documents.
- A withdrawn candidate retains read-only access to their submitted application and eligible uploaded documents while records are retained, but cannot edit or upload.

## Review

- Review queue/detail denies unauthorized, inactive, suspended, and wrong-role callers and excludes terminal states.
- Interview status and bounded notes are recorded through an authorized admin operation.
- Information requests are bounded, audited records and do not expose internal interview notes through candidate contracts.
- Every review decision targets the selected candidate application/attempt and enforces the approved transition from that application's current state; a decision on one application cannot silently change another application for the same candidate.
- Invalid, skipped, candidate-wide, or cross-application status transitions fail.
- Decline requires reason.
- Administrative decisions and candidate-owned withdrawals add status history and audit evidence without overwriting prior history.
- Onboarding assignment is accepted only for the intended application in `conditionally_selected` state and an existing active plan. Earlier/later/terminal application states, another application's selection, inactive plans, and unknown plans are rejected without superseding an existing valid assignment.

## Documents

- Only optional `resume` and `cover_letter` categories exist in Phase 1C; there is no generic or regulated-document category and neither category gates submission.
- Candidate upload accepts only `.pdf`, `.doc`, and `.docx` under the approved 10 MiB policy, requires extension/declared MIME/libmagic/structure agreement, and completes a clean ClamAV scan before object persistence.
- `/api/v1/upload-document` accepts one authenticated candidate-AAL2 PDF/JPEG/PNG up to exactly 5 MiB, never persists bytes, and returns safe 413/415/422/503 failures.
- Scanner unavailability, timeout, malformed response, or non-clean result fails closed and persists no candidate object bytes or metadata.
- Candidate document upload requires AAL2 before and after submission; after-submission uploads are append-only and limited to active application states.
- Private object cannot be fetched anonymously.
- Authorized retrieval is short-lived or proxied.
- Candidate restricted-document view/download requires AAL2 in addition to ownership and lifecycle authorization.
- Candidate cannot retrieve another candidate’s file.
- Issued document version cannot be edited.
- New revision supersedes prior version.
- Acknowledgement references an exact issued version that is assigned to the candidate through the active onboarding assignment; unassigned, superseded-only, cross-candidate, or arbitrary document versions are denied.
- Acceptance/rejection creates audit evidence.

## Onboarding

- Authorized admin can create/list onboarding plans and inspect their task templates.
- Candidate portal navigation exposes the onboarding destination when the candidate has an eligible assignment, and admin portal navigation exposes onboarding administration to authorized administrators; direct routes retain server-side authorization.
- Plan can be assigned only to the intended `conditionally_selected` application and only when the plan is active.
- Candidate can see only their assigned dashboard, submit bounded task evidence, and acknowledge an assigned exact document version.
- Authorized admin can review submitted task evidence and link/update an external e-signature envelope without implementing custom signing.
- Mandatory tasks and configured gates contribute to activation-readiness calculation.
- Only configured activation-gate codes may be satisfied, and gate changes create audit evidence.
- FSRA verification is recorded as administrative evidence, not asserted automatically.
- System provisioning task can be completed manually.
- Satisfying every configured gate may set `activation_ready=true`; it does not change the candidate/application to `active`, create an agent relationship, or represent final activation.
- Final agent activation remains subject to a separately approved administrative or operational workflow; the current implementation does not expose a final activation operation and tests must not claim otherwise.

## Agent profiles

- Draft is private.
- Candidate or agent cannot self-publish.
- Approval is required.
- Editing published content returns the profile to pending approval.
- Suspension requires an authorized admin reason.
- Suspended profile is removed from public directory and direct public rendering.
- Published page contains configured regulatory fields.
- Agent-specific application path uses configured safe mapping.

## Environment and operations

- Live production startup fails with local-file storage.
- Live production startup fails with development auth.
- Live production startup fails with wildcard CORS or remote infrastructure endpoints.
- Health endpoint works without exposing secrets.
- Database health distinguishes API health from database connectivity.
- Logs do not contain tokens or raw document URLs.
- Live production requires private MinIO and fail-closed ClamAV; local filesystem storage and non-production scanner backends are rejected.
- Supabase Studio, when enabled, is local-operator-only; Supabase Storage and its S3 protocol remain disabled.
