# API and Data Inventory

## API routes

### Foundation through Phase 1C

| Method     | Route                                                                     | Access                              | Purpose                                                                                        |
| ---------- | ------------------------------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------------------------- |
| GET        | `/health`                                                                 | Public                              | Process health without dependency detail or secrets.                                           |
| GET        | `/health/db`                                                              | Public                              | Application-database reachability.                                                             |
| GET        | `/api/v1/auth/access?area=candidate\|admin`                               | Authenticated                       | Maps verified Supabase identity to local role, relationship, lifecycle, and MFA authorization. |
| POST       | `/api/v1/leads`                                                           | Public                              | Minimal contact-first inquiry and separate consent evidence.                                   |
| GET        | `/api/v1/leads?limit=&offset=&status=`                                    | Brokerage admin                     | No-store bounded lead queue.                                                                   |
| POST       | `/api/v1/leads/{lead_id}/status`                                          | Brokerage admin                     | No-store status update among `new`, `assigned`, `contacted`, and `closed`, with safe audit evidence. |
| POST       | `/api/v1/leads/{lead_id}/marketing-consent/withdrawal`                    | Brokerage admin                     | Idempotent marketing-only withdrawal.                                                          |
| GET        | `/api/v1/integrations/mortgage-application`                               | Public                              | Current legacy redirect route; scheduled for removal only when the Keeper-native borrower entry path is implemented. |
| GET        | `/api/v1/recruitment/postings`                                            | Public                              | Published recruitment summaries only.                                                          |
| GET        | `/api/v1/recruitment/postings/{slug}`                                     | Public                              | Published posting detail; non-public records return safe `404`.                                |
| POST       | `/api/v1/recruitment/postings/{slug}/applications/start`                  | Verified external identity          | Atomic, narrow candidate provisioning and posting-specific attempt creation.                   |
| GET, POST  | `/api/v1/admin/recruitment-postings`                                      | Brokerage admin                     | No-store list and bounded draft creation.                                                      |
| PATCH      | `/api/v1/admin/recruitment-postings/{posting_id}`                         | Brokerage admin                     | Versioned bounded edit.                                                                        |
| POST       | `/api/v1/admin/recruitment-postings/{posting_id}/{action}`                | Brokerage admin                     | Explicit `publish`, `close`, or `archive` transition with audit evidence.                      |
| GET        | `/api/v1/candidate/privacy-disclosure`                                    | Candidate                           | Server-owned disclosure text/version.                                                          |
| GET        | `/api/v1/candidate/applications`                                          | Candidate                           | Owned posting-specific applications.                                                           |
| GET        | `/api/v1/candidate/applications/status`                                   | Candidate                           | Minimal allow-listed application status.                                                       |
| GET, PATCH | `/api/v1/candidate/applications/{application_id}`                         | Owning candidate                    | Owned read and revision-checked draft update.                                                  |
| POST       | `/api/v1/candidate/applications/{application_id}/submit`                  | Owning candidate                    | Exactly-once submission/privacy/history/audit transaction.                                     |
| POST       | `/api/v1/candidate/applications/{application_id}/withdraw`                | Owning candidate                    | Application-specific audited withdrawal.                                                       |
| GET, POST  | `/api/v1/candidate/applications/{application_id}/documents`               | Owning candidate at AAL2            | Private metadata list and validated clean-before-persistence upload.                           |
| DELETE     | `/api/v1/candidate/applications/{application_id}/documents/{document_id}` | Owning candidate at AAL2            | Draft-only document removal.                                                                   |
| GET        | `/api/v1/documents/{document_id}/download`                                | Owning candidate or brokerage admin | Authorized/audited local response or short-lived private MinIO redirect.                       |
| POST       | `/api/v1/upload-document`                                                 | Active candidate at AAL2            | Non-persisting PDF/JPEG/PNG validation and ClamAV scan, up to exactly 5 MiB.                   |

### Phase 1D review and onboarding

| Method    | Route                                                                                                         | Access           | Purpose                                                                                                       |
| --------- | ------------------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------- |
| GET       | `/api/v1/admin/candidates`                                                                                    | Brokerage admin  | No-store bounded review queue.                                                                                |
| GET       | `/api/v1/admin/candidates/{candidate_id}?application_id={application_id}`                                     | Brokerage admin  | Review detail for one eligible posting-specific attempt.                                                      |
| POST      | `/api/v1/admin/candidates/{candidate_id}/interview`                                                           | Brokerage admin  | Record interview state and bounded internal notes for the body `application_id`.                              |
| POST      | `/api/v1/admin/candidates/{candidate_id}/information-requests`                                                | Brokerage admin  | Create a bounded application-linked information request and lifecycle/audit evidence.                         |
| POST      | `/api/v1/admin/candidates/{candidate_id}/decision`                                                            | Brokerage admin  | Apply a row-locked transition to the body `application_id` with required reason policy.                       |
| POST      | `/api/v1/admin/candidates/{candidate_id}/assign-onboarding?plan_id={plan_id}&application_id={application_id}` | Brokerage admin  | Assign the conditionally selected attempt to an active onboarding plan.                                       |
| GET, POST | `/api/v1/admin/onboarding/plans`                                                                              | Brokerage admin  | List lock-aware plans or create reusable plans with bounded task templates.                                 |
| GET, PATCH | `/api/v1/admin/onboarding/plans/{plan_id}`                                                                   | Brokerage admin  | Retrieve one plan or edit it only while no assignment references it.                                        |
| PATCH     | `/api/v1/admin/onboarding/plans/{plan_id}/availability`                                                       | Brokerage admin  | Change availability only before first assignment; referenced plans are immutable.                           |
| GET       | `/api/v1/admin/onboarding/assignments[/{assignment_id}]`                                                     | Brokerage admin  | List readable exact-application assignments or retrieve assignment-bound tasks, gates, and envelopes.       |
| POST      | `/api/v1/admin/onboarding/candidates/{candidate_id}/tasks/{task_id}/review`                                   | Brokerage admin  | Accept/reject submitted candidate task evidence.                                                              |
| POST      | `/api/v1/admin/onboarding/assignments/{assignment_id}/gates/{code}/satisfy`                                   | Brokerage admin  | Add concise evidence to one of three manual assignment gates; derived gates reject manual assertion.        |
| POST      | `/api/v1/admin/onboarding/assignments/{assignment_id}/gates/{code}/reopen`                                    | Brokerage admin  | Reopen a satisfied manual gate with a required correction reason and append-only evidence event.             |
| POST      | `/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes`                                        | Brokerage admin  | Link one Documenso document for recovery/history; it cannot satisfy readiness or completion.                 |
| POST      | `/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/issue-ica`                              | Brokerage admin  | Issue the configured ICA for the authoritative user, or safely supersede a failed/recovery-only predecessor. |
| POST      | `/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{envelope_id}/refresh`                  | Brokerage admin  | Reconcile status authoritatively from configured self-hosted Documenso.                                      |
| POST      | `/api/v1/admin/onboarding/assignments/{assignment_id}/esign-envelopes/{envelope_id}/replace`                  | Brokerage admin  | Preserve a failed predecessor and link a distinct replacement document.                                     |
| POST      | `/api/v1/admin/onboarding/assignments/{assignment_id}/complete`                                                | Brokerage admin/AAL2 | Revalidate lifecycle and Keeper-issued agreement provenance, then atomically complete and grant agent once. |
| GET       | `/api/v1/admin/onboarding/documents`                                                                          | Brokerage admin  | List controlled documents and current issued versions.                                                        |
| GET       | `/api/v1/candidate/onboarding`                                                                                | Candidate        | Owned assignment, task, gate, document, acknowledgement, and envelope dashboard.                              |
| POST      | `/api/v1/candidate/onboarding/tasks/{task_id}/evidence`                                                       | Owning candidate | Submit bounded task evidence.                                                                                 |
| POST      | `/api/v1/candidate/onboarding/acknowledgements`                                                               | Owning candidate | Record acknowledgement of an eligible exact version assigned through the active application-bound assignment. |

### Phase 1E agent profiles

| Method     | Route                                       | Access          | Purpose                                                                              |
| ---------- | ------------------------------------------- | --------------- | ------------------------------------------------------------------------------------ |
| GET        | `/api/v1/agents`                            | Public          | Published-only safe summaries for eligible active agents.                            |
| GET        | `/api/v1/agents/{slug}`                     | Public          | Published-only safe detail; non-public/ineligible records return `404`.              |
| GET, POST  | `/api/v1/admin/agent-profiles`              | Brokerage admin | List eligible profiles or create a bounded draft for an active agent relationship.   |
| GET        | `/api/v1/admin/eligible-agents`             | Brokerage admin | List readable active agent relationships that do not already have a profile.          |
| GET        | `/api/v1/admin/agent-profiles/slug-availability` | Brokerage admin | Check a validated slug against current and permanently reserved profile slugs.      |
| GET, PATCH | `/api/v1/admin/agent-profiles/{profile_id}` | Brokerage admin | Retrieve/update a profile; editing published content returns it to pending approval. |
| POST       | `/api/v1/agents/{profile_id}/status`        | Brokerage admin | Apply the approval/publication/suspension/archive lifecycle with audit evidence.     |

Production disables OpenAPI. Local and controlled non-production expose `/openapi.json` and `/docs`.

### Borrower routes through Phase D.2

The generated borrower contract mounts:

- `POST /api/v1/borrower-applications/start` — exact-host/origin/CSRF guarded draft start and secure capability cookie;
- `GET /api/v1/borrower-applications/{application_id}` — exact-draft capability read returning the current saved non-SIN payload for same-browser in-memory rehydration with private/no-store controls; primary and co-borrower SIN values are always omitted;
- `PATCH /api/v1/borrower-applications/{application_id}` — exact-draft capability and optimistic typed encrypted save;
- `POST /api/v1/borrower-applications/{application_id}/documents` — pre-parser bounded exact-host/origin/CSRF/capability-cookie guarded multipart upload. Capability verification occurs before multipart parsing. The API permits PDF, PNG, JPEG, DOC, and DOCX up to 25 MiB each, enforces 25 current documents and 250 MiB aggregate plaintext, requires approved category metadata and a bounded description only for `Other`, validates declared MIME/extension/libmagic/format structure agreement, fails closed on ClamAV or private-storage unavailability, encrypts accepted bytes before persistence under opaque object keys, and records safe success/failure result evidence;
- `GET /api/v1/borrower-applications/{application_id}/draft-documents` and `DELETE /api/v1/borrower-applications/{application_id}/draft-documents/{document_id}` — no-store exact-draft metadata listing and explicit removal. Failed removal preserves a retryable pending marker and blocks submission until reconciliation completes;
- `GET /api/v1/borrower-applications/{application_id}/consent` — returns only the newest active consent whose effective interval contains the server time, with no-store response controls;
- `POST /api/v1/borrower-applications/{application_id}/submit` — exact-draft capability, origin, and CSRF guarded final submission. It independently selects that same newest effective consent and requires the supplied version and SHA-256 wording digest to match. Real-data enablement additionally requires the catalog row's explicit owner-approval marker. Submission validates the expected revision and co-borrower coverage, writes exact consent evidence and an immutable encrypted snapshot atomically, transitions to `submitted`, sets seven-year retention, revokes the capability, and returns the original committed result for an identical capability retry;
- `GET /api/v1/borrower-applications/{application_id}/internal` — exact assigned-agent or administrator AAL2 internal projection, gated on durable submission evidence;
- `POST /api/v1/borrower-applications/{application_id}/sin/reveal` — dedicated administrator/AAL2 reveal with bounded reason and safe audit.

Phase E adds the bounded internal review surface:

- `GET /api/v1/borrower-applications/review-queue` — brokerage administrator/AAL2 queue for submitted or under-review applications with durable submission evidence; drafts and terminal records are omitted.
- `POST /api/v1/borrower-applications/{application_id}/assignment` — brokerage administrator/AAL2 assignment or reassignment to a server-validated active agent relationship, with bounded reason and safe assignment/audit evidence. Submitted applications enter `under_review` on assignment.
- `GET /api/v1/borrower-applications/{application_id}/internal` — assigned active exact agent/AAL2 or brokerage administrator/AAL2 masked internal projection; durable submission evidence is required.
- `GET /api/v1/borrower-applications/{application_id}/documents` — assigned active exact agent/AAL2 or brokerage administrator/AAL2 borrower document metadata list without object keys.
- `GET /api/v1/borrower-applications/{application_id}/documents/{document_id}/download` — assigned active exact agent/AAL2 or brokerage administrator/AAL2 API-proxied decrypting document download with private/no-store/nosniff and safe content disposition; no direct, public, or presigned MinIO URL is returned.
- `POST /api/v1/borrower-applications/{application_id}/sin/reveal` — assigned active exact agent/AAL2 or brokerage administrator/AAL2 explicit SIN reveal with bounded reason category and safe reveal audit.

Legal-hold, purge, retention operations, dedicated ingress, browser evidence, and operational readiness remain later-phase work.

No borrower route accepts an arbitrary user/agent ID, public object key, external redirect, marketing consent, typed signature, credit-bureau request, underwriting decision, lender submission, or Filogix operation.

### Phase C borrower browser orchestration

- Exact `apply.localhost:3000` and `apply.keeperfinancial.ca` hosts route to the dynamic `/mortgage-application` page without invoking Supabase borrower identity.
- The browser client uses only the mounted start/get/patch inventory through same-origin, credentialed, `no-store` requests with the borrower CSRF marker. It never reads the capability cookie.
- Only the opaque application ID is retained in `sessionStorage` as a route locator. Application answers and SIN remain in React memory until sent to the API and are not written to browser storage, URLs, analytics, console output, or server-rendered markup.
- Recovery revalidates the opaque ID against the HTTP-only capability cookie and receives only revision/lifecycle plus `has_sin` and `has_co_borrower` redaction flags.
- The web form sends section-shaped partial payloads under the generated `payload: Record<string, unknown>` contract. Current API source validates partial saves with `validate_borrower_draft()` and `save_draft_payload()` deep-merges them into the prior encrypted revision; unknown keys still fail closed.

## Browser authentication and candidate provisioning orchestration

The browser routes orchestrate the existing API inventory; they are not additional FastAPI routes:

1. A published `/careers/{slug}` page links to both `/auth/register?posting={slug}` and `/auth/sign-in?posting={slug}`.
2. Both server-rendered pages re-fetch the public posting and render the flow only when the slug still resolves to a published posting. Repeated, malformed, unknown, closed, and archived context fails closed.
3. Registration supplies `/auth/callback?posting={slug}` as the Supabase email-confirmation redirect. `/auth/callback` exchanges the authorization code for a Supabase SSR cookie session and invokes the application-start API.
4. Posting-bound password submission occurs at `POST /auth/sign-in/submit`. It establishes the cookie session and invokes the same start API. Safe posting context survives bounded credential/provisioning errors; an unavailable posting is discarded.
5. `POST /api/v1/recruitment/postings/{slug}/applications/start` remains the only approved narrow local-provisioning boundary. Before any local mapping is required, the API validates the bearer JWT's ES256/JWKS signature, exact issuer/audience, expiry, UUID subject, and signed email, then uses that same bearer plus the browser-safe public anon key against local Supabase Auth `/user` to require the exact subject/email and an authoritative `email_confirmed_at`. It validates the currently published posting before atomically creating or reusing the local user, identity, candidate role/relationship, and posting-specific application attempt. Provider unavailability fails closed with a bounded `503`.
6. Generic `/auth/sign-in` remains non-provisioning and returns only to an allow-listed portal root. An unmapped identity is still denied by `/api/v1/auth/access`.
7. Next.js `proxy.ts` asks Supabase to validate/refresh protected and auth requests and propagates rotated/deleted cookies. Candidate/admin server access helpers call `getUser()` before consuming the session and then defer all portal authorization to FastAPI/PostgreSQL.

### Local administrator identity and MFA orchestration

- `apps/api/scripts/link_local_admin_identity.py` is a local-operator command, not an API route. It accepts an existing admin email and explicit Supabase Auth user UUID, then transactionally replaces only the known seeded placeholder subject. Its local-only recovery flag can reset only `admin@example.test` back to that seeded placeholder before re-linking. It creates no Auth user, local user, role, or identity and uses no service-role credential.
- `make reset-local-admin` is the bounded local-only recovery wrapper for a mistaken synthetic admin UID link. `make link-local-admin SUPABASE_SUBJECT=<uuid>` is the bounded linking wrapper. The script requires `APP_ENV=local`, exact existing `brokerage_admin` authorization, an active user, and one existing Supabase identity. A genuine non-placeholder subject is rejected by the link path unless the reset wrapper first restores only `admin@example.test` to the placeholder; a subject owned by another user is rejected.
- `/auth/sign-in?returnTo=/admin` is an allow-listed generic, non-provisioning sign-in path. Successful password authentication continues through `/auth/mfa?returnTo=/admin`; the return value is navigation intent only.
- `/auth/mfa` uses the signed-in user's browser session to list, enroll, challenge, and verify a TOTP factor. The API remains authoritative: `/api/v1/auth/access?area=admin` and all `require_admin` operations independently require the mapped active `brokerage_admin` and AAL2 when configured.

The genuine local Supabase/Mailpit registration and existing-user recovery journey is available as an opt-in integration test and passed on 2026-07-18 for the synthetic published posting. Source-level tests cover callback exchange, cookie writes/refresh propagation, expiry denial, posting preservation, authoritative confirmed-user lookup, and generic non-provisioning without requiring the live local identity stack.

## Implemented Phase 1D and Phase 1E data flows

- Review: local authorized admin → application-specific review queue/detail → row-locked interview, information request, or transition service → PostgreSQL application lifecycle/history/audit transaction.
- Onboarding: authorized admin → conditionally selected application plus active unused-or-locked reusable plan → application-bound assignment generation → permanent plan lock → candidate-owned dashboard and assignment-specific evidence/acknowledgement → admin task review, three manual evidence gates, and two derived gates → PostgreSQL records and audit evidence.
- Controlled documents: an assignment snapshots exact currently issued, non-superseded versions → candidate onboarding projection → assignment/version-authorized acknowledgement; any private bytes continue through the authorized MinIO download boundary.
- External e-signature: admin may instantiate one configured template for the exact assignment-linked authoritative user. Keeper first reads the exact configured template and verifies its numeric `id` plus exactly one recipient, the configured signer slot, before it can distribute; it then submits only that template/slot with the deterministic assignment external ID. The documented `/template/use` response must return a bounded string document `id`, `DOCUMENT` type, `TEMPLATE` source, the same external ID, a distributed status, exactly one authoritative-email `SIGNER`, and a signing token or URL validated to one non-empty `/sign/{token}` segment on the configured public origin. Provider refresh must echo the requested document `id` and an allow-listed status. Keeper stores assignment-bound identifiers, URL, and reconciled status through a configured-origin/no-redirect adapter; it does not sign or store signed files. Manual/recovery links and replacements preserve history but cannot satisfy readiness or completion.
- Completion: explicit administrator/AAL2 request → locked exact assignment/application/candidate/user/role/envelope/readiness evidence → activatable submitted-application and nonterminal-relationship revalidation → one transaction completes onboarding, activates the exact application and relationship, retains candidate access, grants the existing agent role once, and appends safe history/audits.
- Agent publication: authorized admin → readable eligible active local agent relationship → draft/update → approval/publication transition → permanent first-publication slug lock/reservation → safe public list/detail projection. Suspension/archive removes the public projection without releasing the slug.
- File acceptance: authenticated AAL2 request → bounded read and type/structure checks → fail-closed ClamAV scan → private MinIO persistence only on clean → PostgreSQL metadata/audit commit. Rejected or unavailable-scan bytes are not persisted.

Candidate document acceptance is intentionally format-specific:

| Extension | Required declared MIME             | Accepted libmagic detection                                                                                       | Required structural proof                                                                                                                                                                                                                                |
| --------- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.pdf`    | `application/pdf`                  | `application/pdf`                                                                                                 | `%PDF-` version header, final EOF with only bounded printable PDF comments after it, readable non-encrypted parser projection, and at least one page.                                                                                                    |
| `.doc`    | `application/msword`               | `application/msword` or `application/x-ole-storage`                                                               | Narrow compound-file Word document stream/FIB plus the selected Word table stream; arbitrary OLE is rejected.                                                                                                                                            |
| `.docx`   | official Office Open XML Word MIME | official DOCX MIME or bounded `application/zip`, `application/x-zip`, or `application/x-zip-compressed` detection | Canonical single-disk ZIP boundaries (including exact standard data descriptors), required OPC/Word parts/content types/relationships, safe package paths, bounded entries/XML/expansion/ratio, supported compression only, and no encryption or macros. |

The upload response exposes safe detail categories rather than parser output:
`unsupported_extension`, `declared_mime_mismatch`,
`detected_mime_mismatch`, `pdf_structure_invalid`,
`docx_structure_invalid`, `legacy_doc_invalid`, `file_too_large`,
`malware_detected`, `scanner_unavailable`, and `storage_unavailable`.
Validation occurs before scanner construction; clean scanning occurs before
MinIO, and metadata is committed only after the private object write.

## Live data services

The authoritative live environment is the local Linux Docker Compose stack. Application/authorization data uses durable `db` PostgreSQL, private object bytes use durable `minio`, and malware decisions use healthchecked local `clamav` with persistent signatures. Metadata remains in PostgreSQL. The local Supabase CLI stack supplies identity only and has its own separate internal database. No hosted Supabase or Cloudflare R2 inventory exists.

## Database models

| Model                                                                                          | Foundation responsibility                                                                                                                                                                                                                              |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `User`, `UserIdentity`                                                                         | Local account and verified Supabase subject link.                                                                                                                                                                                                      |
| `Role`, `UserRole`                                                                             | Application authorization grants.                                                                                                                                                                                                                      |
| `Candidate`, `CandidateApplication`, `CandidateStatusHistory`                                  | Recruitment relationship, required posting-specific application/attempt, controlled revision and application-level state, append-oriented lifecycle evidence. Supports concurrent applications but only one nonterminal attempt per candidate/posting. |
| `RecruitmentPosting`                                                                           | Draft/published/closed/archived opportunity.                                                                                                                                                                                                           |
| `OnboardingPlan`, `OnboardingTask`, `CandidateOnboardingAssignment`, `CandidateOnboardingTask` | Reusable plan editable only before first assignment, application-specific assignment generations, and assignment-bound task state.                                                                                                                     |
| `ProgrammaticGate`, `GateEvidenceEvent`, `CandidateEsignEnvelope`                              | Assignment-bound manual/derived readiness state, append-only manual correction evidence, and provider-reconciled Documenso history including replacements.                                                                                              |
| `ControlledDocument`, `DocumentVersion`                                                        | Logical controlled document and immutable issued-file metadata.                                                                                                                                                                                        |
| `CandidateEmploymentEntry`, `CandidateEducationEntry`                                          | Bounded normalized repeat groups for the approved questionnaire; no unrestricted answer JSON.                                                                                                                                                          |
| `CandidateDocument`                                                                            | Required candidate/application/category linkage plus private random object key, declared/detected MIME, hash, size, current/quarantine/scan status, and timestamps—not object bytes.                                                                   |
| `CandidateOnboardingDocumentVersion`, `PolicyAcknowledgement`                                  | Exact assignment/version authorization plus candidate, actor, wording, and timestamp evidence.                                                                                                                                                         |
| `AgentProfile`                                                                                 | Approval-controlled public profile content, licence/contact/image/social metadata, safe language/service/specialty lists, version/publication evidence, and permanent first-publication slug lock. It contains no borrower or underwriting data.        |
| `LeadInquiry`                                                                                  | Approved minimal contact fields only; server-owned source/status. Queue indexes support `(created_at,id)` and `(status,created_at,id)`.                                                                                                                |
| `ConsentRecord`                                                                                | Server-versioned service or optional marketing evidence, grant time, optional withdrawal time, and trusted capture source.                                                                                                                             |
| `AuditEvent`                                                                                   | Append-oriented safe lead creation, marketing grant/withdrawal, lifecycle, publication, and document event metadata.                                                                                                                                   |

Phase B adds `BorrowerApplication`, `BorrowerApplicationPayload`, `BorrowerConsentRecord`, `BorrowerApplicationSnapshot`, `BorrowerApplicationStatusHistory`, `BorrowerAssignmentHistory`, `BorrowerLegalHold`, and `BorrowerSinRevealAudit`, with existing `AuditEvent` used only for safe high-risk metadata. Phase D.1 adds `BorrowerDocument` and `BorrowerConsentCatalog`, and extends submitted snapshots with payload revision, schema version, ciphertext, and exact consent-record binding. Phase D.2 adds document category/description and retryable removal state, constrains scan-state combinations, and adds the fail-closed `BorrowerConsentCatalog.real_data_approved` release marker. Phase E adds forward migration `20260726_0013`, which records the borrower-document encryption payload revision needed to decrypt document ciphertext with the same purpose/application/revision AAD used at upload time. PostgreSQL stores encrypted payloads and authoritative metadata; private object storage holds encrypted borrower document bytes and submitted snapshot bytes.

UUIDs are primary keys. PostgreSQL check constraints reinforce service statuses. Service code—not client input or database constraints alone—owns valid transitions. Migration `20260724_0011` creates the Phase B borrower tables and indexes from `20260722_0010`; migration `20260726_0012` adds borrower documents, the consent catalog, and D.1 snapshot-binding columns; unissued migration `20260726_0015` adds the D.2 document and consent-release constraints while refusing to invent categories for existing borrower-document rows. The source chain has one verified `20260726_0015` head; a disposable PostgreSQL upgrade and model-drift check remain required. Mortgage deal, credit-bureau, automated underwriting, lender submission, deal-compliance, full CRM, commission, and payroll models remain excluded.

Migration `20260715_0003` brings the schema into conformance with `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`: posting and immutable source provenance are mandatory, attempt/application lifecycle is distinct, the questionnaire/disclosure are version-controlled, and every new candidate document has explicit application/category linkage. The migration refuses to invent provenance or linkage for incompatible legacy rows.

Migration `20260717_0005` creates the previously missing `agent_profiles` table, chained from `20260716_0004`. Its columns, status check, user foreign keys, unique user/slug boundaries, and publication index match the SQLAlchemy model.

Forward migration `20260717_0006` adds application provenance for review and
onboarding, application-bound assignment/task/history relationships, and the
exact assignment/document-version join. Legacy rows remain nullable when the
correct application or assignment cannot be proved; new mutation paths reject
that ambiguity.

Forward migration `20260718_0007` resolves the bounded Phase 1D metadata/schema
drift without rewriting `0001` through `0006` or changing API behavior. It
preserves candidate-first creation-order indexes for e-sign envelopes,
information requests, and programmatic gates; removes only the assignment
index duplicated exactly by the assignment-generation unique constraint; and
expresses `ON DELETE RESTRICT` for candidate-task templates, populated task
reviewers, and acknowledged document versions. Reviewer nullability remains
available for unreviewed tasks.

Forward migration `20260719_0008` binds gate, policy-acknowledgement, and e-sign evidence to exact onboarding assignments; adds append-only gate evidence and envelope replacement history; and adds permanent profile slug-lock evidence. Ambiguous legacy candidate-scoped rows are not guessed into satisfying assignment evidence. Upgrade refuses duplicate non-null legacy provider envelope IDs before DDL rather than choosing a row. Historical profile publication is recovered from current state/timestamps or authoritative publication audit events. Downgrade refuses rejected-envelope rows before DDL because `0007` cannot represent that evidence without a lossy relabel.

Forward data migration `20260722_0009` repairs only active, ownership-consistent exact assignments whose derived `policy_acknowledgement` gate is open while no required assigned policy version lacks an exact-assignment acknowledgement. It creates no acknowledgement row and does not rewrite historical assignments. Its downgrade is intentionally a no-op because reopening repaired gates could erase valid derived state established after upgrade.

Forward data migration `20260722_0010` configures the existing `agent` role required by explicit onboarding completion. It inserts only the role definition with conflict-safe semantics and creates no user-role grant. Its downgrade is intentionally a no-op because authorized completion may grant the role after upgrade and deleting it would destroy valid authorization relationships.

## Contract generation

Phase D.2 adds public exact-capability routes for active consent,
draft-document metadata/removal, categorized upload, and caller-idempotent
submission. These routes remain exact-origin/CSRF/no-store boundaries and do
not replace the separate internal assigned-agent/administrator AAL2 document
routes. Forward migration `20260726_0015` adds non-null borrower document
category and nullable bounded `Other` description with a fail-fast
non-falsifying legacy-row preflight. It also adds a nullable
`deletion_pending_at` recovery marker so object deletion and metadata/audit
commit failures remain retryable, block submission, and cannot strand an
apparently downloadable row. The source chain has one head.

FastAPI/Pydantic owns the OpenAPI contract. `make openapi` exports it and runs `openapi-typescript` to create TypeScript declarations. Generated output should change in the same review as API schema changes.

`packages/contracts/src/index.ts` exports generated `paths`, `operations`, and `components` while retaining the hand-authored `PortalArea`. Public posting and published-agent operations have no bearer declaration; provisioning, candidate, document, and administration operations declare HTTP bearer security. Candidate and public-agent response schemas structurally omit internal reason/note/actor/audit/decision and unpublished lifecycle fields.

## 2026-07-18 browser-completion API addendum

- `GET /api/v1/candidate/onboarding/availability` is the no-store minimal navigation projection. It returns `{ "available": false }` when no current application-bound assignment exists; this is not a grant of onboarding access.
- `GET /api/v1/candidate/onboarding` returns the owned dashboard or a stable empty dashboard with `assignment=null` and `activation_ready=false`. Direct candidate authorization remains mandatory.
- `POST /api/v1/admin/candidates/{candidate_id}/information-requests` retains the candidate-id route family for compatibility but the body requires the exact `application_id`. Only `under_review` and `interview` are eligible; success transitions that same attempt to `more_information_required` with history/audit evidence.
- `/auth/mfa` accepts the admin root, candidate root, or exact `/candidate/applications/{uuid}#documents`. Candidate completion refreshes the Supabase session and reconfirms AAL2; document APIs separately require role, ownership, eligible lifecycle/category, and AAL2.
