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
- At 100% zoom, 320, 375, 768, 1024, 1280, 1366, 1536, and 1920 CSS-pixel
  viewports have no horizontal overflow; header, hero, trust strip, and
  following content share coherent centered alignment, and the hero focal
  content remains visible.
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

The redirect assertions above characterize the currently implemented Phase 1B boundary. Borrower implementation must remove that route/path only when the replacement tests below pass; no temporary arbitrary redirect is acceptable.

## Borrower application

Phase B source tests cover the model/migration/encryption/capability/typed-draft/internal-authorization subset below and prove that no successful public submission or capability revocation is available without the Phase D coordinator. Document, final-submission, retention/purge, UI, genuine-browser, deployment, and operational criteria remain unfulfilled; passing Phase B tests is not owner acceptance.

- `apply.keeperfinancial.ca` is an exact Keeper-owned origin from the same repository; unknown hosts, reflected origins, wildcard CORS, and untrusted forwarded host/proto fail closed.
- Starting a draft returns a high-entropy capability only in a secure host-only HTTP-only same-site cookie; only a keyed digest persists and no capability appears in response JSON, URL, logs, analytics, or audit.
- Missing, wrong, expired, submitted, replayed, cross-application, and cross-origin capabilities are denied without revealing whether another application exists.
- One primary borrower is required and no more than one co-borrower is accepted. Unknown fields, invalid repeat counts, negative amounts, invalid dates, and malformed contact/address data fail typed server validation.
- Required SIN passes nine-digit and Luhn validation, encrypts before persistence, is never returned to the borrower, is masked internally, and is absent from logs, errors, audits, traces, URLs, notifications, and search indexes.
- Assigned-agent and administrator denial matrices include anonymous, identity-only, inactive, wrong-role, unassigned agent, other assigned agent, AAL1, suspended/offboarded, stale assignment, and invalid lifecycle. Only the exact active assigned agent or administrator at AAL2 succeeds.
- SIN reveal is a separate AAL2 operation with a bounded reason and safe one-time audit; list/detail payloads do not reveal it by default.
- Attribution accepts only a server-resolved eligible public slug. Invalid/unpublished/suspended attribution enters the unassigned queue. Reassignment is administrator/AAL2, reasoned, and audited.
- Borrower document categories include `Other`; technical tests cover PDF/DOC/DOCX/JPEG/PNG agreement, 25 MiB/file, 25-file, 250 MiB aggregate limits, empty/malformed/polyglot/archive/executable/macro/encrypted rejection, ClamAV detection/outage/timeout/protocol failure, encryption failure, storage failure, metadata rollback, object cleanup, private access, and cross-application denial.
- Submission rejects an absent, stale, caller-supplied, or unapproved privacy/credit-use consent version and contains no marketing or signature field.
- Submission is atomic and idempotent: it returns success only after immutable encrypted snapshot and database evidence are durable; retry returns the same result; object/database failure does not clear the browser or expose an orphan.
- Successful submission revokes the borrower capability and prevents borrower post-submission reads/edits.
- Draft inactivity expires/purges at 30 days. Submitted retention is exactly seven calendar years from original submission; amendment/review does not reset it. Active legal hold blocks purge, and release restores the original deadline.
- Purge covers PostgreSQL, MinIO, projections, caches, and ordinary backup expiry, is idempotent, alerts on partial failure, and is proven after isolated restore before serving traffic.
- Genuine browser evidence uses synthetic borrowers and safe generated documents only and covers keyboard, focus/error summaries, responsive reflow, cookie flags, no-store/cache behavior, duplicate submission, scanner/storage failures, assignment isolation, and console/network inspection.

## Lead administration

- `GET /api/v1/leads` and marketing withdrawal deny anonymous, unmapped identity, mapped identity-only, inactive, wrong-role, candidate, and admin-without-required-MFA callers; an active verified AAL2 admin is allowed.
- The list is no-store, maximum 100 rows per request, offset-paginated, newest-first by `created_at` then `id`, and accepts only lifecycle status filtering.
- Queue URLs contain only safe page/status values; list output contains the necessary lead fields and explicit service/marketing consent states and timestamps.
- Withdrawal affects only the lead’s marketing consent, preserves `granted_at`, sets `withdrawn_at` once, is idempotent, and never changes service acknowledgement.
- First withdrawal creates exactly one `marketing_consent.withdrawn` audit with actor, request ID, target consent ID, and safe capture source. Unknown lead or absent marketing consent returns a safe `404`.
- Lead, service consent, optional marketing consent, and audits roll back together on persistence failure.
- Request logs and audit metadata exclude contact fields, message, tokens, raw payloads, and private URL/query values.

## Authentication and authorization

The 2026-07-17 remediation adds focused API/web coverage for the following
criteria plus an opt-in genuine local Supabase/Mailpit integration journey.
The integration journey is not replaced by mocked component assertions.

- Anonymous user cannot access candidate or admin routes.
- Authenticated identity without local application access is denied.
- Every published posting exposes both registration and existing-user sign-in, and each path preserves the validated posting slug through authentication to the posting-specific application-start operation.
- Registration confirmation exchanges the callback code for a genuine Supabase session, persists the server/browser cookie session, invokes the narrow posting-bound provisioning operation exactly once, and enters the resulting application.
- Posting-bound password sign-in authenticates the existing Supabase identity, then invokes the same narrow application-start operation for the preserved published posting; retries are idempotent and do not duplicate the local user, role, candidate, or application attempt.
- Generic sign-in remains non-provisioning: without a posting context, a confirmed but locally unmapped identity is denied candidate access and receives no local user, role, candidate, or application relationship.
- A confirmed but locally unmapped existing user can recover only by returning to a published posting and using its posting-bound sign-in path; closed, archived, unknown, or malformed posting context fails closed without provisioning.
- Posting-bound start does not require a pre-existing `UserIdentity`, candidate role, or `Candidate`. It first validates ES256/JWKS signature, exact issuer/audience, expiry, UUID subject, and signed email, then confirms the same subject/email and `email_confirmed_at` through local Supabase Auth `/user`. User-editable metadata is not verification evidence; mismatch or provider ambiguity fails closed before the atomic local transaction.
- Session cookies survive the callback and subsequent server/browser requests; valid refresh rotates cookies without losing authorization, while expired, revoked, or invalid sessions return to sign-in without leaking tokens or granting access.
- Candidate can access only own record and documents.
- Candidate cannot access internal notes.
- Candidate cannot access another candidate by changing an identifier.
- Admin action requires correct role.
- Local admin identity linking requires explicit `APP_ENV=local`, a normalized existing active admin email, an existing exact `brokerage_admin` grant, one existing Supabase identity whose subject is the known seeded placeholder, and an explicit valid Supabase UUID. It is transactional and idempotent; it rejects a duplicate subject, genuine non-placeholder replacement, invalid input, missing prerequisites, and non-local execution.
- `/auth/sign-in?returnTo=/admin` is discoverable and may select only the allow-listed admin portal root. Return intent never creates an application user, identity, role, or relationship and never elevates a candidate, identity-only, or unmapped account.
- An authenticated local admin at AAL1 is directed through the browser TOTP enrollment/challenge workflow and remains denied by `/api/v1/auth/access?area=admin` and protected admin operations. Only an active verified local `brokerage_admin` whose current token is AAL2 succeeds.
- TOTP enrollment and verification use only the authenticated browser session and public Supabase client configuration; service-role credentials, provider payloads, tokens, cookies, and setup secrets are not logged. Provider failures render bounded recovery guidance.
- Suspended/offboarded account is denied.
- Role revocation takes effect.

## Candidate application

- Candidate saves draft.
- Saving disables duplicate action, preserves the visible scroll/focus
  context, and announces saving/saved/validation/network/stale-revision status
  beside the controls through `aria-live="polite"`.
- The application section outline is nonsticky informational content unless it
  is implemented as real accessible navigation; noninteractive sticky text is
  prohibited.
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

These criteria now apply to `CandidateApplication` attempts rather than the
candidate relationship row.

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
- Common readable PDFs may contain bounded printable PDF comments after the
  final EOF marker; binary/polyglot tails, missing/truncated structure, unreadable
  pages, and encryption remain rejected. DOCX accepts the official detected MIME
  or bounded ZIP-family detection only when strict OPC/WordprocessingML proof
  succeeds, including safe paths, required parts, bounded expansion, no
  encryption, and no macro-enabled content.
- Candidate upload failures expose only the safe categories
  `unsupported_extension`, `declared_mime_mismatch`,
  `detected_mime_mismatch`, `pdf_structure_invalid`,
  `docx_structure_invalid`, `legacy_doc_invalid`, `file_too_large`,
  `malware_detected`, `scanner_unavailable`, and `storage_unavailable` (plus
  bounded category/name/empty-file input categories). Validation, scanning, or
  storage failure never reports success or leaves candidate metadata/private
  object bytes.
- `/api/v1/upload-document` accepts one authenticated candidate-AAL2 PDF/JPEG/PNG up to exactly 5 MiB, never persists bytes, and returns safe 413/415/422/503 failures.
- Scanner unavailability, timeout, malformed response, or non-clean result fails closed and persists no candidate object bytes or metadata.
- Candidate document upload requires AAL2 before and after submission; after-submission uploads are append-only and limited to active application states.
- Confirmed AAL2 automatically loads owned document metadata into an explicit
  loading/list/empty/retry state. Clean upload refreshes that list, prevents
  duplicates while pending, preserves category, and resets only the file
  input. Invalid files, malware, scanner outage, storage outage, and MFA denial
  have distinct bounded responses without false success.
- Private object cannot be fetched anonymously.
- Authorized retrieval is short-lived or proxied.
- Candidate restricted-document view/download requires AAL2 in addition to ownership and lifecycle authorization.
- Candidate cannot retrieve another candidate’s file.
- Issued document version cannot be edited.
- New revision supersedes prior version.
- Acknowledgement references an exact issued version that is assigned to the candidate through the active onboarding assignment; unassigned, superseded-only, cross-candidate, or arbitrary document versions are denied.
- Acceptance/rejection creates audit evidence.

## Onboarding

The current assignment contract carries both `application_id` and
`assignment_id`; task and acknowledgement evidence is evaluated within that
assignment generation.

- Authorized admin can create/list onboarding plans, author and reorder initial tasks, and edit an unused plan's name, description, ordered tasks, and availability.
- The first assignment reference permanently locks the plan. Content, task order, and availability changes then fail with conflict and the administrator UI shows the locked state without mutation controls.
- Candidate portal navigation exposes the onboarding destination when the candidate has an eligible assignment, and admin portal navigation exposes onboarding administration to authorized administrators; direct routes retain server-side authorization.
- Plan can be assigned only to the intended `conditionally_selected` application and only when the plan is active.
- Candidate can see only their assigned dashboard, submit bounded task evidence, and acknowledge an assigned exact document version.
- Authorized admin can review submitted task evidence and link a self-hosted Documenso document to the exact assignment without implementing custom signing.
- Documenso refresh is provider-authoritative, uses only the configured HTTPS origin without redirect following, and fails closed on malformed, unavailable, redirected, or unrecognized provider responses.
- A rejected, voided, or recovery-only current envelope can be superseded through bounded Keeper issuance without deleting its predecessor, and only after provider success. Only a verified current `completed` Keeper-issued envelope with validated template/external-ID/recipient provenance satisfies executed-agreement readiness; manual/recovery links never do.
- Mandatory tasks and the five configured assignment-bound gates contribute to activation-readiness calculation.
- Only `background_check`, `fsra_authorization`, and `system_provisioning` accept concise manual evidence. Reopening one requires a correction reason and append-only evidence; `policy_acknowledgement` and `executed_agreements` are derived-only and reject manual assertion or reopening.
- An assignment with no required issued policy versions automatically projects `policy_acknowledgement=satisfied`; it creates no acknowledgement row. An assigned required version keeps that gate open until the candidate records the exact-assignment acknowledgement.
- FSRA verification is recorded as administrative evidence, not asserted automatically.
- System provisioning task can be completed manually.
- Satisfying every configured gate may set `activation_ready=true`; it does not change the candidate/application to `active`, create an agent relationship, or represent final activation.
- One configured ICA template can be issued only to the exact assignment-linked active user's authoritative email, with no recipient override. Before distribution, the adapter requires the configured template response to echo its numeric ID and contain only the configured `SIGNER` slot. The documented issuance response must then provide a bounded document ID, `DOCUMENT` type, `TEMPLATE` source, deterministic assignment external ID, exactly one authoritative-email `SIGNER`, and a validated same-origin signing token or URL. Missing configuration or an incompatible provider response creates no local envelope; a failed reissue leaves the predecessor current.
- Candidate signing is exposed only from the current non-superseded Keeper-issued envelope through a validated same-origin `/sign/{token}` URL with one non-empty token segment; predecessor and non-actionable URLs are never exposed.
- An administrator with an AAL2 principal can explicitly complete only the exact active, activation-ready assignment with an activatable submitted application, nonterminal candidate relationship, and current provider-synced Keeper-issued completed envelope. AAL2 remains mandatory even when broader admin-MFA enforcement is disabled. The transaction completes the assignment, activates the exact application and candidate relationship, retains the candidate role, grants the existing agent role once, and appends status/audit evidence exactly once.
- The migration chain and local seed configure the existing `agent` role definition without adding any `user_roles` grant. Missing role configuration fails completion closed with an actionable administrator error rather than being misreported as stale readiness.
- Repeated and concurrent completion is idempotent; any failure rolls back status, role, history, and audit changes together. Completed assignments remain read-only candidate/admin history and make an otherwise profile-less user eligible for agent-profile administration.

## Agent profiles

- Draft is private.
- Candidate or agent cannot self-publish.
- Profile creation selects only a server-projected eligible active agent relationship; ordinary operator UI does not require raw user/profile UUID entry.
- Slug availability is server-checked. The first successful publication permanently locks and reserves the slug, including after unpublishing; subsequent slug mutation fails server-side and the UI disables it.
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

## 2026-07-18 browser-completion acceptance addendum

- A candidate without an onboarding assignment receives `available=false` and an empty stable onboarding projection, can continue using the application portal, and does not enter a full-dashboard request/render loop. Onboarding navigation appears only after an authorized current assignment.
- Every material frontend rule is visible before submission; the interest minimum is counted, employment months are canonical `YYYY-MM`, ineligible referral detail cannot remain hidden in the payload, and safe API `422` details map to linked field errors while preserving values.
- Candidate document AAL1 exposes candidate-scoped TOTP enrollment or challenge, refreshes the session after verification, proves AAL2, and returns only to the exact allow-listed owned application document section. Candidate MFA never grants admin authorization.
- Information request requires the exact selected `application_id`, is enabled only for `under_review` or `interview`, transitions only that attempt, and returns an operation-specific conflict for all other states. Candidate status exposes only the bounded open request message for that application, never internal interview notes.
- Permanent onboarding authorization/not-found responses are not automatically retried. Transient direct-dashboard failures expose one bounded manual retry.
