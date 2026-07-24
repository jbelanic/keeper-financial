# Borrower Application MVP Requirements

- **Decision date:** 2026-07-24
- **Status:** owner-approved product, architecture, security, privacy, and lifecycle requirements
- **Implementation status:** not implemented at this documentation checkpoint
- **Keeper baseline:** `5f8a41f34bb3586c59d613848fafc9435a86b50d`
- **Legacy reference:** `jbelanic/MortgageApp` at `251077177315ade4a94d12eb62df750684ed2bb7`

This document is the current phase specification for the Keeper-native borrower application. It reverses the former external-application boundary. It is an engineering requirements document, not legal advice, a privacy opinion, a credit-bureau authorization, or production approval.

## 1. Approved outcome

Keeper Financial will become the system of record for the MVP borrower mortgage-application intake and its supporting documents. The same Keeper repository and release process will serve the public site and `https://apply.keeperfinancial.ca`.

The MVP includes:

- one primary borrower and zero or one co-borrower;
- mortgage request, applicant, employment, property, asset, liability, note, consent, and supporting-document intake;
- encrypted drafts, immutable submitted snapshots, lifecycle metadata, consent evidence, attribution, assignment, retention, legal holds, and audit evidence;
- authenticated review by the assigned active mortgage agent and brokerage administrators;
- private MinIO object storage and fail-closed ClamAV scanning;
- local-first validation followed by a separately authorized self-hosted Linux deployment.

The MVP does not redirect, hand off, export, or integrate with Filogix or another origination provider. A future Filogix export/import or API integration requires a separate owner decision after the product's documented capabilities are assessed.

## 2. Scope exclusions

This approval does not add:

- credit-bureau connectivity or automated credit pulls;
- automated underwriting, eligibility, approval, rate, lender-network, or compliance decisions;
- lender submission, deal-compliance workflow, closing workflow, commission, payroll, or a full client CRM;
- borrower accounts, borrower MFA, cross-device resume, emailed resume links, or a post-submission borrower portal;
- electronic signatures, typed-name signatures, agreement authoring, or signed-document storage;
- marketing consent, marketing automation, or application-payload notifications;
- arbitrary internal-user access, shared-agent access, or public/private-object URLs;
- production deployment, shared-database mutation, live-secret creation, or legacy-repository archival during the documentation phase.

Agent identity verification of a client from application data and documents is an operational review activity. Keeper must not claim that document upload proves identity or that Keeper performs automated identity verification.

## 3. Actors and authorization

### 3.1 Borrower

A borrower does not create a Keeper account. Starting an application creates an opaque server-owned application ID and a separate high-entropy capability secret. The browser receives the capability only in a `Secure`, `HttpOnly`, host-only, `SameSite=Strict` cookie. PostgreSQL stores only a keyed digest.

The capability:

- authorizes only the exact draft;
- is combined with exact-host/origin validation and CSRF protection;
- supports same-browser resume only;
- never appears in URLs, logs, analytics, email, audit payloads, or browser storage;
- expires after 30 days of draft inactivity;
- is revoked permanently on successful submission.

Draft start sets server-owned `last_activity_at`. Thereafter, only a successful exact-capability-authorized borrower mutation that commits a new draft payload revision or changes the current document set updates it. Reads/resume, no-op or failed saves, failed capability/access attempts, internal agent/administrator access, malware scanning, and other background processing do not extend draft retention.

A borrower can update only the current draft and cannot retrieve previously saved SIN values. The controlling borrower enters any co-borrower information with that person's authority; there is no separate co-borrower invitation or shared access in the MVP. No borrower self-service access exists after submission.

### 3.2 Assigned mortgage agent

An internal agent must have an active Keeper user, verified Supabase identity, current `agent` role/relationship, and AAL2. The agent can access only applications assigned to that exact user. Publication of an agent profile is not itself authorization to view applications.

### 3.3 Brokerage administrator

A brokerage administrator requires the existing active `brokerage_admin` authorization and AAL2. Administrators can access the application queue, assign or reassign applications with a reason, manage legal holds, and perform other expressly defined operations. Each sensitive read or mutation requires server-side authorization and safe audit evidence.

### 3.4 Attribution and assignment

A public `agent` slug may be captured only after server-side resolution to a current eligible active agent profile. Client-supplied user IDs are rejected. A valid preference may produce initial assignment; an invalid, unpublished, suspended, or unknown slug is discarded and the application enters the unassigned administrator queue. Reassignment is administrator/AAL2 only, requires a reason, and is audited. Attribution and assignment remain distinct fields.

## 4. Data collection contract

The server owns a versioned, typed schema. Unknown fields are rejected. Empty optional groups are omitted rather than stored as unrestricted JSON. Free text is length-bounded and treated as sensitive.

### 4.1 Mortgage request

| Field                                        | Requirement                                                                              |
| -------------------------------------------- | ---------------------------------------------------------------------------------------- |
| purpose/transaction type                     | Required allow-listed value such as purchase, refinance, renewal/switch, or pre-approval |
| estimated property value or requested amount | Required positive decimal as applicable to purpose                                       |
| expected closing date                        | Optional; required only when applicable and must be a valid date                         |
| down-payment sources                         | Repeatable when applicable; source, positive amount, and bounded description for `Other` |
| preferred agent slug                         | Optional public input; resolved server-side and never trusted as a user ID               |

### 4.2 Primary borrower and co-borrower

Exactly one primary borrower is required. At most one co-borrower is allowed. Each present borrower has the same typed structure except that relationship to primary is required only for the co-borrower.

| Field                                                  | Requirement                                                                       |
| ------------------------------------------------------ | --------------------------------------------------------------------------------- |
| legal first and last name                              | Required, bounded Unicode text                                                    |
| email and phone                                        | Required and structurally validated                                               |
| preferred contact method                               | Required allow-listed value                                                       |
| date of birth                                          | Required valid past date                                                          |
| SIN                                                    | Required nine digits with Luhn validation; specially protected as described below |
| marital status                                         | Required allow-listed value                                                       |
| number of dependants                                   | Required non-negative integer                                                     |
| relationship to primary                                | Required for co-borrower only                                                     |
| current address, city, province/territory, postal code | Required and structurally validated                                               |
| years and months at address                            | Required non-negative duration                                                    |

Previous-address collection is deferred. If an operating requirement later requires a minimum address-history period, the owner must approve that additional data before implementation.

### 4.3 Employment and income

Each borrower requires at least one current income/employment entry. Additional entries are allowed within server-configured bounds.

| Field                                | Requirement                                                                               |
| ------------------------------------ | ----------------------------------------------------------------------------------------- |
| occupation/category and industry     | Required allow-listed values with `Other`                                                 |
| employer/business name and job title | Required bounded text as applicable                                                       |
| employment/income type               | Required allow-listed value, including employed, self-employed, retired, and other income |
| duration                             | Required non-negative years/months                                                        |
| annual gross income                  | Required non-negative decimal                                                             |
| employer address                     | Optional for MVP                                                                          |

The workflow records borrower-declared information. It does not verify employment or income automatically.

### 4.4 Subject property

Subject-property details are optional for pre-approval and required when the transaction has an identified property.

| Field group                                    | Requirement                       |
| ---------------------------------------------- | --------------------------------- |
| address, city, province/territory, postal code | Required when property identified |
| property type, style, age, occupancy           | Required when property identified |
| livable area and unit                          | Optional bounded positive values  |
| property taxes, heating, condo fees            | Optional non-negative amounts     |
| lot and garage details                         | Optional typed values             |

### 4.5 Other properties and mortgages

Other-property entries are optional and bounded. Each entry can contain address, purchase date/price, estimated value, occupancy, and repeatable mortgage balances, payments, frequency, and maturity date. The server rejects negative amounts and implausible dates. The original legacy limit is reference only; the Keeper limit is an implementation configuration documented and tested before release.

### 4.6 Assets and liabilities

Assets and liabilities are optional repeatable groups but the borrower must explicitly confirm whether each group is complete. Asset entries contain an allow-listed type, positive value, and bounded description when needed. Liability entries contain type, current balance, payment amount/frequency, and bounded description when needed.

### 4.7 Notes

One optional additional-notes field is allowed, is length-bounded, is encrypted with the application payload, and carries a warning not to enter passwords, authentication secrets, or unrelated third-party personal information.

## 5. SIN controls

Collecting SIN is owner-approved because it is required for the mortgage agent's credit-assessment workflow. It receives heightened controls:

- encrypt before persistence with authenticated application-level encryption;
- never store in plaintext columns, browser persistence, object metadata, filenames, logs, traces, analytics, audit payloads, URLs, email, or notifications;
- do not index or search it;
- do not return a saved value to the borrower;
- show only a masked value to internal reviewers by default;
- require an explicit AAL2 reveal operation by the assigned agent or administrator;
- audit the reveal using application ID, actor ID, reason/category, result, and timestamp, never the SIN;
- prevent generic serializers, exception handlers, and telemetry from including it.

The implementation must use a reviewed cryptographic library and the encryption/key-custody design below. It must not invent cryptographic primitives.

## 6. Consent

Immediately before submission, the controlling borrower must actively accept one unchecked-by-default, server-versioned privacy and credit-use consent for the brokerage's use of the application to assess the request and help find an appropriate mortgage product. Evidence records the exact immutable consent version, application ID, named borrower coverage, acknowledgement time, capture source, safe capability-session reference, and submission revision. The MVP does not claim separate co-borrower assent; the exact approved wording must address the controlling borrower's authority to provide co-borrower information.

The consent is not an electronic signature and includes no marketing consent. A preselected checkbox, bundled optional marketing, typed-name signature, or client-supplied consent version is prohibited.

The exact production wording is not approved by this engineering decision. Local implementation may use conspicuously synthetic draft wording, but real-data submission must remain disabled until the owner supplies or approves exact wording and immutable version after appropriate professional review.

## 7. Documents

There is no narrow business-category restriction. The initial categories are income/employment, banking/investment, down payment, property, tax, identification, other, and any later owner-approved display labels. `Other` keeps the business workflow open without accepting technically unsafe bytes.

Initial technical policy:

- accepted formats: PDF, DOC, DOCX, JPEG, and PNG;
- maximum 25 MiB per file;
- maximum 25 current documents per draft;
- maximum 250 MiB total current document bytes per draft;
- no archives, executables, scripts, macro-enabled Office files, password-protected/encrypted files, malformed files, or polyglots;
- extension, declared MIME, libmagic MIME, and format-specific structure must agree;
- upload is scanned fail-closed by ClamAV before encryption and private persistence;
- scanner, validation, encryption, storage, or metadata failure leaves no available object and returns a bounded safe error;
- original filenames are sensitive display metadata, not object keys or logs;
- download is authenticated, authorized, audited, API-proxied decryption with `private, no-store`, `nosniff`, safe content disposition, and no public or direct presigned MinIO URL.

The exact limits are owner-approved MVP defaults, must be configuration-bounded, and may be changed later only with capacity and security review.

## 8. Persistence and cryptography

### 8.1 PostgreSQL

PostgreSQL is authoritative for draft metadata and encrypted typed payloads, lifecycle, revision, capability digest, attribution, assignment, document metadata, consent evidence, retention dates, legal holds, and audit references.

### 8.2 MinIO

A dedicated private borrower bucket or least-privilege namespace stores encrypted document bytes and immutable encrypted submission snapshots. Supabase Storage remains disabled. Submitted snapshot object keys are random or deterministic opaque identifiers and never contain names, email, SIN, filenames, or other personal data.

### 8.3 Encryption

Use AES-256-GCM through a maintained reviewed library, unique random 96-bit nonces, authenticated metadata that binds ciphertext to application/object purpose, versioned key IDs, and integrity verification before plaintext use. New writes use the active key; old keys remain available for authorized reads until a separately approved re-encryption and retirement operation completes.

Active and historical keys are supplied outside Git from root-owned read-only files or an equivalent deployment secret mount. Environment variables may name key IDs and file paths but must not contain or expose key material. Key backup, offline recovery, rotation, compromise response, and restore validation are release gates. Volume encryption and encrypted backups are additional controls, not substitutes for application-level encryption.

## 9. Lifecycle

Allowed application states are:

`draft -> submitted -> under_review -> completed`

Additional terminal paths are `withdrawn` and `expired`. State transitions are explicit server-side operations with row locks/revision checks and safe history/audit evidence.

- Drafts expire and are purged when 30 days have elapsed since the server-owned `last_activity_at` defined in Section 3.1.
- Successful submission revokes the borrower capability and creates an immutable encrypted MinIO snapshot.
- A submitted snapshot is never overwritten.
- No borrower post-submission editing exists in the MVP.
- A later internal correction must be an append-only administrator/AAL2 revision with reason and preserved prior snapshot; that correction operation is deferred until separately specified.
- `retention_due_at` is exactly seven calendar years from original successful submission and never resets because of review or amendment.
- A legal hold applies only to a submitted application, prevents its automated purge, and does not broaden access. It cannot be applied to a draft or extend the mandatory 30-day abandoned-draft purge.
- Submitted-application legal-hold placement/release is administrator/AAL2 only, requires a bounded reason and audited timestamp, and preserves prior evidence.
- Expired submitted records are purged from PostgreSQL, MinIO, search projections, caches, and ordinary backups according to the approved retention job and backup policy. Failures alert and retry without partial silent completion.

Encrypted backups use a rolling 30-day retention unless a later approved operational policy changes it. A restored system must run overdue purge before serving traffic.

## 10. Submission transaction

Submission must be atomic and idempotent from the caller's perspective:

1. authenticate the exact capability and lock the draft;
2. validate the full typed payload, document readiness, attribution, and exact consent version;
3. encrypt and write a new immutable snapshot object;
4. commit submission metadata, consent evidence, lifecycle history, retention date, capability revocation, and audit evidence;
5. return success only after durable object and database completion.

Retries return the same completed submission result. If object creation succeeds but the database transaction does not, cleanup/reconciliation must prevent an orphan from becoming available. The system must never clear the browser or report success while persistence is still asynchronous or uncertain.

## 11. Host, TLS, browser, and network boundary

- `https://keeperfinancial.ca/apply` is the public choice/entry page.
- `https://apply.keeperfinancial.ca` is the dedicated borrower origin served from the Keeper web application.
- Caddy is the approved self-hosted ingress recommendation for exact-host routing, HTTPS, and HTTP-to-HTTPS redirect.
- Only the ingress exposes public ports 80/443.
- API, PostgreSQL, MinIO, ClamAV, Supabase Studio, MinIO Console, and administrative provider surfaces remain on private container networks or explicit loopback operator bindings.
- CORS and CSRF origin allow-lists are exact; wildcards and reflected origins are prohibited.
- Production borrower cookies are secure, HTTP-only, host-only, same-site strict, narrowly scoped, rotated when required, and omitted from logs.
- Forwarded-host/proto/client-IP values are trusted only from the configured ingress.
- Security headers, no-store responses, request-size limits, timeouts, rate limits, and bot mitigation are required before public exposure.

Local development may use an explicit loopback/apply-localhost origin, but production security must not be weakened to accommodate local testing.

## 12. Audit and observability

Required safe events include draft start, draft update, failed capability access category, document upload/scan/storage result, submission, assignment/reassignment, application view, document download, SIN reveal, lifecycle transition, legal-hold placement/release, retention purge, and purge failure.

Audits and logs contain opaque IDs, actor, action, result, bounded reason/category, version, and timestamp only. They exclude application answers, names, contact data, SIN, filenames, object URLs, capability values, keys, consent prose, document contents, and provider/browser tokens.

Operational metrics use aggregate counts and latencies. No analytics SDK may receive borrower payloads.

## 13. Migration from MortgageApp

The legacy repository is a UX and schema reference only. Keeper will not import its Kotlin/Ktor backend, browser local-storage persistence, Discord webhook, permissive CORS, Turnstile implementation, hard-coded API paths, secret-shaped values, unversioned JSON persistence, or typed-name signature.

No legacy production data import is approved or assumed. The standalone repository remains unarchived until Keeper implementation, local acceptance, self-hosted deployment, and cutover are owner-accepted. Archive is non-destructive and preserves history.

## 14. Acceptance boundary for implementation phases

No implementation phase is accepted solely because unit tests pass. Evidence must cover:

- schema/migration and generated-contract alignment;
- exact capability authorization and cross-application denial;
- assigned-agent/admin authorization and AAL2;
- SIN encryption, masking, reveal auditing, and redaction;
- ClamAV and object-storage fail-closed behavior;
- idempotent/atomic submission;
- consent version enforcement;
- retention/legal-hold behavior;
- exact-host, cookie, CSRF/CORS, rate-limit, and cache controls;
- genuine browser flows with synthetic identities/documents;
- backup and isolated restore before live release;
- final diff and documentation reconciliation.

## 15. Stop conditions

Stop implementation rather than inventing an answer when:

- exact production consent wording/version is required for real-data enablement but remains unapproved;
- a new sensitive data class, borrower collaboration model, third-party integration, credit-bureau operation, underwriting decision, lender submission, or e-signature is requested;
- key custody, restore access, public DNS/TLS, operator ownership, or legal-hold authority is unresolved for deployment;
- the design would expose plaintext SIN/documents outside the narrow authorized request;
- authorization would rely on client IDs, profile publication, possession of a URL, or Supabase identity alone;
- scanner or encryption unavailability would be handled by accepting data;
- historical evidence or issued migrations would need rewriting;
- real personal data would be needed to prove behavior before approval.

## 16. Phase sequence

1. **Phase A:** synchronize authority and requirements only.
2. **Phase B:** models, migration, encryption, capability, lifecycle, internal authorization, OpenAPI/contracts, tests.
3. **Phase C:** Keeper-native borrower form and same-browser draft flow.
4. **Phase D:** borrower documents and immutable submission snapshots.
5. **Phase E:** agent/admin review, assignment, secure display/download, SIN reveal.
6. **Phase F:** retention/legal hold, ingress, local browser evidence, backup/restore, deployment readiness.
7. **Phase G:** owner-approved cutover and legacy repository archival.

Each implementation phase requires one bounded prompt, one dedicated worktree, explicit tests/evidence, documentation updates, and owner acceptance before materially expanding scope.
