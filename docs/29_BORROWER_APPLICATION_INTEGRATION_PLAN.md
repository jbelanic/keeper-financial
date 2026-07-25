<!-- Repository copy of the owner-approved Borrower Application Integration Plan. Authoritative source: .hermes/plans/2026-07-24_101428-approved-borrower-application-integration-plan.md (approved 2026-07-24). Created as docs/29 per the Phase B completion report, which reserved this number for the approved-plan repository copy. Do not edit independently of the approved source. -->

# Approved Borrower Application Integration Plan

> **For Hermes:** Before implementation, load `test-driven-development`, create one dedicated worktree/branch, and produce one consolidated bounded implementation prompt for the approved phase. Do not run implementation concurrently with another writer.

**Goal:** Make Keeper Financial the self-hosted system of record for full borrower mortgage applications and borrower documents, porting the useful MortgageApp workflow into the existing Keeper Financial monorepo while retiring the separate legacy repository after accepted cutover.

**Architecture:** Reimplement the approved MortgageApp workflow in Keeper’s existing Next.js/FastAPI modular monolith; do not deploy or vendor the legacy Ktor service. Store mutable encrypted drafts and lifecycle/authorization metadata in PostgreSQL. On submission, create an immutable, versioned, application-encrypted canonical application snapshot in private MinIO; store borrower documents as separately encrypted private MinIO objects after strict validation and fail-closed ClamAV scanning. Present the workflow at `https://apply.keeperfinancial.ca` through the same self-hosted release and an exact-host reverse proxy.

**Tech Stack:** Next.js 16, React 19, TypeScript, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, MinIO/S3, ClamAV, Supabase Auth for internal staff, AES-256-GCM application encryption, Docker Compose, Caddy reverse proxy, OpenAPI-generated TypeScript contracts, Vitest, Pytest, Ruff, mypy, Playwright/real-browser evidence where already supported.

**Planning baseline:** `keeper-financial` `main` at `5f8a41f34bb3586c59d613848fafc9435a86b50d`; legacy `MortgageApp` `main` at `251077177315ade4a94d12eb62df750684ed2bb7`.

---

## 1. Owner-approved decisions recorded from 2026-07-24

The owner has approved the following product decisions. They supersede conflicting living-document restrictions once synchronized through Phase A.

1. Keeper Financial becomes the system of record for full borrower mortgage applications and borrower documents.
2. The MVP has no Filogix handoff, import, export, or API integration. Filogix interoperability is a future option only after its supported capabilities are assessed.
3. The application collects SIN because mortgage agents require it for an external credit-checking process. Keeper does not itself add credit-bureau connectivity in this MVP.
4. The bounded MVP supports exactly one primary borrower and zero or one co-borrower. Additional co-borrowers require a later schema and UX decision.
5. Borrowers and co-borrowers do not receive Keeper accounts or MFA in this MVP. Agent verification of identity remains a human brokerage process based on the submitted application and documents.
6. The application has no marketing consent and no Keeper electronic-signature workflow.
7. Submission requires one server-versioned privacy and credit consent acknowledgement for brokerage use of the application to help the client seek an appropriate mortgage product.
8. Submitted records are retained for seven years from the original submission timestamp and then purged unless an active legal hold excludes them from purge.
9. Keeper remains self-hosted on the approved Linux/Docker topology.
10. After accepted integration and cutover, the separate MortgageApp repository may be archived. It is not deleted.

## 2. Lead-architect decisions made under the owner’s delegation

### 2.1 MVP boundary

Keeper is the authoritative intake, document, consent, assignment, review, and retention system for this MVP. It is **not yet**:

- a credit-bureau integration;
- an automated credit-decision or underwriting engine;
- a lender-submission platform;
- a Filogix integration;
- a deal-compliance platform;
- a custom electronic-signature system;
- a commission/payroll system; or
- an automated product-approval, rate, eligibility, or suitability decision maker.

Mortgage agents conduct credit checks and downstream mortgage work outside Keeper for the MVP. Keeper may record safe workflow status and notes but must not claim or infer that a credit check, approval, or regulatory verification occurred automatically.

### 2.2 Borrower access without borrower identity accounts

“No borrower identity/MFA” does not permit an unprotected draft API. The bounded accountless design is:

- A public start endpoint creates a draft and a cryptographically random 256-bit application capability.
- The browser receives the capability only in a `Secure`, `HttpOnly`, host-only, `SameSite=Strict` cookie scoped to `apply.keeperfinancial.ca`; the raw capability is never stored in PostgreSQL, logs, URLs, analytics, or MinIO.
- PostgreSQL stores only a keyed digest of the capability and its expiry.
- Every draft read, save, upload, delete, and submit operation requires the cookie, an exact allowed Origin/Host, CSRF protection, an active draft, and constant-time capability verification.
- The MVP supports same-browser resume while the capability cookie remains valid. It has no cross-device resume, email magic link, shared co-borrower access, or post-submission borrower portal.
- The primary borrower enters co-borrower information with the co-borrower’s authority. A separate co-borrower collaboration/invitation flow is deferred.
- Once submitted, the capability is revoked and the public browser cannot retrieve the application or its documents.

Internal brokerage access remains identity-based. Active `brokerage_admin` users may access all applications. Only the assigned active `agent` may access an assigned application. Both require Supabase identity, application-database authorization, and AAL2 for borrower applications, documents, and SIN reveal.

### 2.3 Agent attribution and assignment

- `?agent=<published-agent-slug>` is a preference signal, not client-controlled authorization.
- The server resolves the slug only against a currently published profile backed by an active agent relationship.
- A valid preference initially assigns the application to that active agent; an absent, invalid, unpublished, suspended, or stale slug results in an unassigned application rather than a failure or guessed match.
- The exact source slug/profile/agent and assignment time are recorded server-side.
- A brokerage administrator may assign or reassign an application to an eligible active agent with a required reason and append-oriented audit evidence.
- Assigned agents can see only their assigned borrower applications. Agents cannot self-assign or enumerate unassigned applications.
- Assignment changes do not alter the original attribution provenance.

### 2.4 Domain and network topology

- Production application origin: `https://apply.keeperfinancial.ca`.
- Public site origin: `https://keeperfinancial.ca` with optional `www` redirect.
- Add one pinned Caddy container as the only public ingress on ports 80/443.
- Caddy routes both domains to the existing Next.js web container and routes same-origin `/api/*` requests to FastAPI. The API, web container port, PostgreSQL, MinIO, MinIO console, ClamAV, Supabase Studio, and local operator services remain internal or loopback-only.
- Next.js middleware rewrites requests received for the exact application host to the borrower application route group. It rejects unexpected forwarded hosts rather than trusting arbitrary proxy headers.
- Application browser calls are same-origin. No wildcard CORS is introduced. Exact production and local origins are configured separately.
- Capability cookies are host-only and are not shared with the public site.
- Local development uses an exact documented local application origin, preferably `http://apply.localhost:3000`, without weakening production TLS/cookie validation.

### 2.5 Encryption and key custody

Because the application contains SIN and financial documents, database credentials and private bucket policy alone are insufficient.

- Add application-layer AES-256-GCM authenticated encryption using the pinned Python `cryptography` package.
- Use a versioned key ring. Production keys are random 32-byte values stored in root-owned files outside Git and mounted read-only into the API container through Docker secrets/files. Environment variables contain only key IDs and file paths, never key material.
- Every encrypted payload/object uses a fresh random nonce and authenticated context containing the application ID, object type, schema version, and key ID to prevent ciphertext substitution across records.
- New writes use the active key; old keys remain available for seven-year records until their data has been purged or explicitly re-encrypted.
- Back up the key ring separately from the encrypted data, with restricted offline custody. A backup without its matching key version is a failed backup.
- Use encrypted Linux host storage/full-disk encryption and encrypted backups in addition to application encryption.
- Scan and validate plaintext document bytes first, encrypt only after a clean ClamAV result, persist ciphertext to MinIO, and decrypt only inside the authorized API response path.
- Do not expose borrower objects through direct presigned MinIO URLs because application-layer ciphertext requires authenticated API decryption. Downloads are API-proxied with `private, no-store`, `nosniff`, safe content disposition, and audit evidence.

### 2.6 SIN controls

- Collect SIN for each primary and co-borrower applicant as an approved required field.
- Validate normalized nine-digit syntax and the SIN Luhn checksum server-side.
- Encrypt the full SIN at the field/payload boundary. Never index, search, log, audit, email, include in URLs, or expose it in ordinary list/detail projections.
- Draft responses return only `sin_provided` and masked last four digits after a successful save. A borrower may replace a SIN but cannot retrieve the previously stored full value.
- Internal screens mask SIN by default. Full reveal requires assigned-agent or administrator authorization, AAL2, a deliberate reveal action, `no-store`, and a dedicated audit event containing IDs and reason/category only—not the SIN.
- Credit checking remains outside Keeper; no credit score or bureau response is stored unless a later approved phase defines that new data flow.

### 2.7 Document policy

The owner’s “no restrictions” decision is interpreted as no narrow business-category allow-list: borrowers may upload any legitimate document relevant to their application and may choose `Other` with a bounded description. It does **not** waive technical security controls.

Initial technical policy:

- Allowed formats: PDF, DOC, DOCX, JPEG, and PNG.
- Reject archives, executables, scripts, HTML/SVG, macro-enabled Office files, password-protected/encrypted files, malformed/polyglot files, and unsupported formats.
- Maximum 25 MiB per file, 25 documents per application, and 250 MiB aggregate plaintext size per application. Values are configuration-controlled with fail-closed upper bounds.
- Business categories: identification, income/employment, bank/investment, down payment, property, tax, credit/liability, and `other`; no category is mandatory in the first MVP unless the form requirements explicitly make it so.
- `other` requires a plain-text description with a strict bounded length; filenames and descriptions never become object keys.
- Every upload requires active draft capability or authorized internal access, strict extension/declared-MIME/libmagic/structure agreement, fail-closed ClamAV, a random borrower object key, encryption before MinIO persistence, PostgreSQL metadata, and rollback cleanup.
- Original filenames are sanitized display metadata only and are never logged or included in audit metadata.

### 2.8 Retention and legal hold

- Drafts that have never been submitted expire and are purged 30 days after their last activity. This is the architect’s minimum-risk default because the approved seven-year trigger begins at submission.
- Submitted applications, all application revisions, consent evidence, documents, object metadata, assignment/history records, and borrower-specific audit references receive `retention_due_at = submitted_at + 7 years` based on the original submission timestamp.
- Amendments or workflow status changes do not reset the seven-year clock.
- An active legal hold blocks purge across PostgreSQL and MinIO. Applying or releasing a hold requires administrator AAL2, a bounded reason/reference, timestamp, actor, and append-oriented audit evidence.
- A scheduled daily purge job selects due, non-held records in bounded batches, deletes MinIO ciphertext objects, then deletes or de-identifies PostgreSQL records according to referential rules. Failures remain retryable and must not mark records purged prematurely.
- Retain one non-personal purge tombstone containing application UUID, purge timestamp, object/row counts, and safe result status; it contains no names, contacts, SIN, filenames, notes, or payload.
- Encrypted backups use a 30-day rolling retention so purged records age out predictably; restore procedures must re-run due purge before a restored environment can serve traffic.

### 2.9 Consent

- No marketing consent is shown or recorded in this workflow.
- No typed-name or checkbox is represented as an electronic signature.
- Submission requires one explicit unchecked-by-default acknowledgement of an immutable server-owned privacy/credit-consent version.
- Evidence stores application ID, exact consent version, acknowledgement timestamp, capture source, and safe capability-session identifier/digest reference. It does not store a signature claim.
- The exact consent text must be owner-supplied and professionally reviewed before processing real borrower data. Engineering may implement the versioned mechanism with synthetic/draft wording locally, but production/pilot use stops until exact wording is approved.

## 3. Data architecture

### 3.1 PostgreSQL records

Create a bounded borrower module rather than mixing borrower models into candidate lifecycle logic:

- `BorrowerApplication`: opaque UUID, state, schema version, revision, capability digest/expiry, attribution and assignment IDs, timestamps, submission/retention/hold fields, and encrypted-draft payload reference.
- `BorrowerApplicationPayload`: application ID, revision, payload schema version, encryption key ID, nonce, ciphertext, plaintext digest, and timestamps. The payload is a canonical typed JSON projection covering mortgage details, primary/co-borrowers, addresses, employment, assets, liabilities, subject property, other properties, and bounded notes.
- `BorrowerDocument`: application ID, business category/description, sanitized filename, declared/detected MIME, plaintext/ciphertext size and digests, MinIO object key, encryption key ID/nonce, scan status/version, lifecycle status, and timestamps.
- `BorrowerConsentRecord`: exact server-owned consent version and acknowledgement evidence.
- `BorrowerApplicationSnapshot`: immutable submitted snapshot object key, payload schema version, key ID/nonce, plaintext/ciphertext digests and sizes, and creation timestamp.
- `BorrowerApplicationStatusHistory`: append-oriented transitions with actor/capability source and safe reason metadata.
- `BorrowerAssignmentHistory`: immutable original attribution plus administrator assignment/reassignment history.
- `BorrowerLegalHold`: active/released evidence with administrator actor and bounded reason/reference.
- Existing `AuditEvent`: safe high-risk events only; no payload, SIN, contact data, filenames, consent text, capability, object key, or private URL.

Use one forward Alembic migration from the current single head at implementation time. Do not rewrite issued migrations or invent data migration from the legacy app because no approved production data migration source has been identified.

### 3.2 MinIO records

Use a dedicated private bucket such as `keeper-borrower-private`, initialized idempotently with anonymous access disabled. Use least-privilege API credentials restricted to that bucket. Object classes:

- `borrower-documents/<random>` — encrypted borrower documents;
- `borrower-submissions/<random>` — encrypted immutable canonical application snapshots.

Object keys contain no application ID, name, email, SIN, filename, agent slug, or document category. PostgreSQL is the only mapping from application to object.

### 3.3 Submission consistency

Submission is idempotent and fail closed:

1. Lock the draft application and verify active capability, exact revision, required fields, document state, and current consent version.
2. Canonicalize and validate the typed payload server-side.
3. Encrypt and write a new immutable snapshot to MinIO.
4. In one PostgreSQL transaction, create snapshot metadata/consent/history/audit evidence, set `submitted_at` and `retention_due_at`, transition to `submitted`, and revoke the capability.
5. If the database transaction fails, delete the just-written snapshot. If cleanup fails, record a safe orphan reconciliation event/metric without exposing the object key publicly.
6. If the transaction commits but the response is lost, a repeated request returns the existing submitted result and never creates a second submission.

## 4. Repository and legacy-source strategy

- Do not add `MortgageApp` as a Git submodule or retain the Ktor backend as another service.
- Do not merge the insecure legacy tree into production `main`.
- Create `docs/migrations/mortgage-app-import-manifest.md` recording source URL, exact source commit, source inventory, known security findings, and a feature-by-feature port/reject/defer mapping.
- Port the form concepts and approved field semantics into Keeper-native code. Do not copy Discord handling, Basic auth, browser local storage, tracked credentials, Turnstile logging/validation defects, hard-coded localhost endpoints, Docker `latest` tags, or unversioned JSON persistence.
- After accepted source, browser, storage, retention, and local deployment evidence—and only under separate GitHub repository-setting authority—archive `jbelanic/MortgageApp` as read-only. Preserve its Git history in that archived repository; no subtree-history import is needed.

## 5. Delivery phases

One implementation prompt should not attempt the entire program. Use one dedicated worktree and one consolidated prompt per owner-approved phase.

### Phase A — Authority synchronization and legacy manifest

**Objective:** Replace obsolete living-document restrictions with the approved borrower-system boundary before code implementation.

**Files:**

- Modify `AGENTS.md` without discarding the owner’s existing uncommitted edits; reconcile the stray punctuation and removed restrictions into coherent current authority.
- Modify `docs/00_PROJECT_SOURCE_OF_TRUTH.md`.
- Modify `docs/01_PRODUCT_VISION_AND_SCOPE.md`.
- Modify `docs/02_PHASE_1_MVP_REQUIREMENTS.md` only where it is a living current requirement; preserve genuinely historical phase statements as dated scope.
- Modify `docs/03_ARCHITECTURE_BASELINE.md`.
- Modify `docs/04_SECURITY_PRIVACY_COMPLIANCE_BASELINE.md`.
- Modify `docs/05_DOMAIN_MODEL_AND_LIFECYCLES.md`.
- Modify `docs/07_DELIVERY_PLAN.md`.
- Modify `docs/08_ACCEPTANCE_TESTS.md`.
- Modify `docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md` with a dated owner decision superseding decisions 2, 3, 5, 8, and 9 only to the extent stated here.
- Modify `docs/11_ENVIRONMENT_VARIABLES.md` for planned settings only after names are finalized.
- Modify `docs/12_THREAT_MODEL.md`.
- Modify `docs/13_API_AND_DATA_INVENTORY.md`.
- Modify `docs/14_TEST_STRATEGY.md`.
- Modify `docs/15_KNOWN_LIMITATIONS.md`.
- Modify `docs/26_PHASE_1F_PRODUCTION_AND_CONTROLLED_PILOT_READINESS_PLAN.md` so borrower data is no longer an automatic stop condition and borrower security/readiness evidence is added.
- Create `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md` as the current implementation specification.
- Create `docs/migrations/mortgage-app-import-manifest.md`.

**Rules:**

- Do not rewrite historical implementation reports (`docs/16_*` through `docs/25_*`, `docs/27_*`) as though they originally covered this decision. Add a dated post-decision note only where a historical exclusion could reasonably be mistaken for current authority.
- “Remove restrictions” means remove obsolete external-provider/custom-application prohibitions. It does not mean delete authentication, authorization, privacy, encryption, malware scanning, retention, legal-hold, logging-minimization, backup, accessibility, or fail-closed requirements.
- Record the exact remaining exclusions: no Filogix/bureau/lender integration, underwriting automation, custom signature, marketing, or deployment under this planning approval.

**Acceptance:** Every living document agrees that Keeper is the borrower application/document system of record; every sensitive-data control and seven-year/legal-hold rule is explicit; historical reports remain historically accurate; no implementation begins from contradictory authority.

### Phase B — Secure borrower foundation

**Objective:** Implement encrypted draft/session, data models, lifecycle, internal authorization, and generated contracts before porting the full UI.

**Create:**

- `apps/api/src/keeper_api/models/borrower.py`
- `apps/api/src/keeper_api/schemas/borrower_applications.py`
- `apps/api/src/keeper_api/services/borrower_crypto.py`
- `apps/api/src/keeper_api/services/borrower_applications.py`
- `apps/api/src/keeper_api/services/borrower_authorization.py`
- `apps/api/src/keeper_api/api/routes/borrower_applications.py`
- `apps/api/tests/test_borrower_crypto.py`
- `apps/api/tests/test_borrower_applications.py`
- `apps/api/tests/test_borrower_authorization.py`
- One forward Alembic migration with the next valid revision.

**Modify:**

- `apps/api/src/keeper_api/models/__init__.py`
- `apps/api/src/keeper_api/api/router.py`
- `apps/api/src/keeper_api/core/config.py`
- `apps/api/src/keeper_api/services/auth.py` to add an internal `agent` portal authorization boundary with AAL2, without weakening candidate/admin behavior.
- `apps/api/pyproject.toml` to pin `cryptography`.
- OpenAPI and `packages/contracts/src/generated.ts`.

**TDD slices:**

1. RED/GREEN AES-GCM round trip, nonce uniqueness, wrong context/key/ciphertext rejection, key rotation read compatibility, and secret-safe errors.
2. RED/GREEN public start with exact Origin/Host, CSRF design, capability digest storage, cookie attributes, rate limiting, and no raw capability in logs/responses/database.
3. RED/GREEN draft ownership: correct cookie reads/saves; missing, malformed, expired, revoked, or cross-draft capability receives safe denial.
4. RED/GREEN typed payload validation including primary/co-borrower cardinality, SIN syntax/Luhn, bounded text/numbers/dates, and `extra="forbid"` mass-assignment rejection.
5. RED/GREEN encrypted payload revisions and stale revision conflict.
6. RED/GREEN administrator-all and assigned-agent-only access with AAL2; identity alone, unassigned agents, suspended agents, and cross-assignment access fail safely.
7. RED/GREEN dedicated masked/full SIN projections and audited AAL2 reveal.
8. RED/GREEN lifecycle: `draft -> submitted -> under_review -> completed|withdrawn`; submitted payload is immutable except append-only internal amendment revisions approved later in this plan.
9. RED/GREEN OpenAPI security declarations and generated contracts.
10. RED/GREEN PostgreSQL migration, constraints, indexes, one Alembic head, and clean `make migrate-check`.

**Stop conditions:** Raw capability/SIN/payload reaches logs or audit; production can start without key files; ciphertext can be substituted across records; an agent can enumerate or access unassigned/other-agent applications; migrations have more than one head.

### Phase C — Keeper-native borrower form

**Objective:** Port the approved MortgageApp form experience into the existing Next.js design system without sensitive browser persistence.

**Create:**

- `apps/web/app/(borrower)/mortgage-application/layout.tsx`
- `apps/web/app/(borrower)/mortgage-application/page.tsx`
- `apps/web/app/(borrower)/mortgage-application/borrower-application-form.tsx`
- Bounded section components under `apps/web/app/(borrower)/mortgage-application/components/`.
- `apps/web/lib/borrower-application-api.ts`
- `apps/web/tests/borrower-application.test.tsx`
- `apps/web/tests/borrower-application-api.test.ts`

**Modify:**

- `apps/web/proxy.ts` for exact application-host routing without mixing Supabase borrower identity into the accountless flow.
- `apps/web/lib/routes.ts`.
- `apps/web/app/(public)/apply/page.tsx`.
- `apps/web/lib/site-config.ts`.
- Shared styles/components only where required.

**Ported field groups:**

- mortgage purpose, requested/estimated amount, property value and closing/maturity context;
- one primary borrower and zero or one co-borrower, including legal name, contact, date of birth, SIN, marital/dependent details, and current/prior address as required;
- employment and income;
- assets and liabilities;
- subject property and existing owned properties/mortgages;
- bounded additional notes;
- agent preference provenance; and
- versioned privacy/credit consent acknowledgement.

The exact required/optional matrix must be enumerated in `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md` before implementation. Do not infer it solely from legacy client-side validation.

**TDD/browser slices:**

1. Start and recover same-browser draft through secure server state.
2. Save each form section with revision handling and clear accessible error summary/focus.
3. Ensure no application payload or SIN enters `localStorage`, `sessionStorage`, URL, analytics, console, server-rendered HTML, or Next cache.
4. Render saved SIN only as masked/provided state; allow replacement without retrieval.
5. Add/remove co-borrowers and repeat groups with stable accessible labels/keys.
6. Handle network/server failure without advancing, clearing, or falsely confirming success.
7. Require current consent only at submission; no marketing or signature UI.
8. Confirm success only after the API reports committed submission; revoke browser access afterward.
9. Test keyboard operation, focus, live errors, 320 CSS-pixel reflow, zoom, and no colour-only state.

**Acceptance:** The useful MortgageApp flow is available from Keeper source, but its MUI dependency, localStorage model, duplicate localhost APIs, Discord path, typed signature, and unsafe consent behavior are absent.

### Phase D — Encrypted MinIO documents and immutable submission snapshot

**Objective:** Make MinIO the private object system for encrypted borrower documents and submitted application snapshots.

**Create:**

- `apps/api/src/keeper_api/services/borrower_storage.py`
- `apps/api/src/keeper_api/services/borrower_documents.py`
- `apps/api/src/keeper_api/schemas/borrower_documents.py`
- `apps/api/src/keeper_api/api/routes/borrower_documents.py`
- `apps/api/tests/test_borrower_documents.py`
- `apps/api/tests/test_borrower_submission.py`
- `apps/web/app/(borrower)/mortgage-application/components/document-upload.tsx`
- `apps/web/tests/borrower-documents.test.tsx`

**Modify:**

- `apps/api/src/keeper_api/services/storage.py` only to extract reusable safe primitives; preserve candidate behavior.
- `apps/api/src/keeper_api/services/document_scan_gate.py` and validators only through additive borrower format support.
- `apps/api/src/keeper_api/middleware/sensitive_uploads.py` to support capability-cookie upload syntax and bounds without weakening bearer-protected candidate routes.
- `apps/api/src/keeper_api/main.py` for exact route limits.
- `compose.yaml` and `.env.example` for dedicated bucket/credentials and encryption-key file settings.
- `docs/11_ENVIRONMENT_VARIABLES.md` and `docs/LOCAL_DEVELOPMENT.md`.
- Forward migration/OpenAPI/contracts.

**TDD slices:**

1. Deny unauthenticated/cross-draft/expired/submitted uploads before multipart parsing.
2. Enforce per-file, count, and aggregate limits.
3. Validate allowed extension, declared MIME, libmagic MIME, and safe structure for PDF/DOC/DOCX/JPEG/PNG.
4. Reject macros, encryption/password protection, polyglots, malformed files, decompression/expansion abuse, executables, archives, and unknown types.
5. Fail closed for stale/unavailable/error ClamAV and prove no MinIO object or metadata persists.
6. Encrypt after clean scan, persist ciphertext under random keys, and verify plaintext/ciphertext digests.
7. Delete ciphertext on metadata transaction failure and reconcile synthetic orphans.
8. List only safe metadata; never return object keys/nonces/private URLs.
9. Proxy authorized decrypting download to capability owner during draft and assigned agent/admin after submission, with safe headers/audit.
10. Generate one canonical encrypted MinIO snapshot during idempotent submission; prove database/MinIO failure cannot produce false success or duplicate submission.
11. Verify anonymous MinIO access and direct plaintext retrieval fail.

### Phase E — Internal borrower application review and assignment

**Objective:** Let authorized administrators and assigned mortgage agents review applications securely.

**Create:**

- `apps/api/src/keeper_api/api/routes/borrower_review.py`
- `apps/api/src/keeper_api/services/borrower_review.py`
- `apps/api/src/keeper_api/schemas/borrower_review.py`
- `apps/api/tests/test_borrower_review.py`
- `apps/web/app/(admin)/admin/borrower-applications/page.tsx`
- `apps/web/app/(admin)/admin/borrower-applications/borrower-application-queue.tsx`
- `apps/web/app/(agent)/agent/layout.tsx`
- `apps/web/app/(agent)/agent/borrower-applications/page.tsx`
- `apps/web/app/(agent)/agent/borrower-applications/[applicationId]/page.tsx`
- `apps/web/lib/borrower-review-api.ts`
- Corresponding web tests.

**Modify:**

- Portal access/proxy/navigation code to add the active-agent/AAL2 internal area without changing candidate/admin authorization semantics.
- Existing agent eligibility projection/service where reuse is safe.

**TDD slices:**

1. Admin queue shows no-store safe summaries and excludes SIN/full payload/doc keys.
2. Assigned agent sees only assigned applications; unassigned and other-agent records return safe denial/404.
3. Valid public agent preference is resolved and snapshotted; invalid preference becomes unassigned.
4. Administrator assignment/reassignment requires eligible active agent, reason, row lock, history, and audit.
5. Detail decrypts the current immutable submitted snapshot only after authorization.
6. SIN remains masked until dedicated AAL2 reveal; reveal is audited and never cached.
7. Documents download only through authorized decrypting API proxy.
8. Status transitions are explicit and audited; no automatic credit/approval/underwriting claim.
9. Concurrent assignment/reassignment/review races preserve one authoritative assignment and history.

### Phase F — Retention, legal hold, backup, and local deployment integration

**Objective:** Make the seven-year system of record operable and safely deployable on the owner’s Linux host.

**Create:**

- `apps/api/src/keeper_api/services/borrower_retention.py`
- `apps/api/scripts/purge_borrower_records.py`
- `apps/api/tests/test_borrower_retention.py`
- `infrastructure/caddy/Caddyfile`
- Approved backup/restore and purge runbooks under `docs/operations/`.

**Modify:**

- `compose.yaml` to add pinned Caddy, private service networking, borrower bucket init, read-only encryption-key mounts, and health dependencies.
- `apps/api/src/keeper_api/core/config.py` for production fail-closed validation.
- `Makefile` for safe dry-run/run/verification commands where appropriate.
- Current readiness, environment, local-development, threat, test, and limitation documents.

**TDD/operational slices:**

1. Compute calendar-correct seven-year `retention_due_at` from original submission.
2. Purge 30-day abandoned drafts and their MinIO objects.
3. Skip active legal holds and prove hold/release requires administrator AAL2/reason/audit.
4. Purge due records in bounded idempotent batches; partial MinIO/database failures retry safely.
5. Produce non-personal purge tombstones only.
6. Prove backup key/data pairing, encrypted backup, 30-day backup expiry, isolated restore, object/metadata reconciliation, and post-restore due purge.
7. Prove only Caddy exposes public 80/443; internal services fail from untrusted interfaces.
8. Prove exact TLS hosts, forwarded-host handling, local/production origin separation, cookie attributes, CSRF, and no wildcard CORS.
9. Exercise ClamAV freshness/failure alerts, MinIO privacy, key-file absence/wrong key, database/MinIO restore, and fail-closed startup.
10. Run genuine synthetic browser journeys from public Get Started through agent review without real borrower data.

**Deployment boundary:** Completing local source and local Docker evidence does not itself change DNS, issue public certificates, deploy to the self-hosted server, migrate a shared database, or authorize real borrower data. Those actions occur later with the owner’s explicit operational assistance request and a verified rollback/backup plan.

### Phase G — Legacy repository archival

**Objective:** End separate active repository management after accepted Keeper cutover.

**Prerequisites:** Keeper implementation accepted; full validation green; migration manifest committed; local and deployed synthetic journeys passed; rollback available; no active legacy write path/data dependency.

**Steps:**

1. Verify the legacy repository still points at recorded commit/history and contains no unpreserved required source.
2. Update its README/archive notice if the owner authorizes that remote write.
3. Archive `jbelanic/MortgageApp` through GitHub repository settings under explicit authority.
4. Verify archive/read-only state and Keeper links/configuration no longer depend on the legacy deployment.
5. Do not delete the legacy repository or rewrite its history.

## 6. Cross-phase validation gates

Every code phase must run applicable repository commands and record actual output:

- `npm run test`
- `npm run lint`
- `npm run typecheck`
- `npm run format:check`
- `npm run build`
- `npm run audit:ci`
- `make test`
- `make lint`
- `make typecheck`
- `make migrate-check` for model/schema work
- deterministic OpenAPI and generated-contract regeneration
- one Alembic head and expected current revision
- `git diff --check`
- dependency and secret scans without printing secrets
- focused PostgreSQL concurrency tests
- MinIO/ClamAV/encryption fail-closed integration tests
- genuine browser accessibility and end-to-end synthetic journeys
- final diff review against every phase acceptance criterion
- exact final `git status`

No test may use a real SIN, genuine borrower document, real credit data, production secret, or public private-object URL. Use clearly synthetic values that pass validation.

## 7. Required source-completion evidence

Each phase completion report must separate:

- confirmed files changed;
- exact source revision/branch/worktree;
- migrations and generated-contract changes;
- exact commands, exit codes, counts, warnings, and failures;
- authorization and cross-account denial evidence;
- encryption/MinIO/ClamAV failure evidence;
- documentation synchronized;
- browser/accessibility evidence;
- unresolved risks and deferred scope;
- operational actions not performed; and
- exact Git status.

Passing tests is necessary but not sufficient for accepting real borrower-data operation.

## 8. Remaining blocker before real-data use

The product scope is approved, but one content decision cannot be manufactured by engineering: the exact privacy and credit-consent wording/version. The mechanism can be implemented and tested with conspicuous synthetic draft wording locally. Real borrower submission must remain disabled until the owner supplies or explicitly approves the exact wording after appropriate professional review.

## 9. Recommended first execution

The first executable unit should be **Phase A only**: synchronize authority and create the borrower MVP specification/import manifest. After reviewing and accepting Phase A, create a separate consolidated prompt for Phase B. Do not start by copying legacy code or editing the database schema while living documents still prohibit the new system of record.
