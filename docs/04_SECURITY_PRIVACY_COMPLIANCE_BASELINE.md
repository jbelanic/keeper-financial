# Security, Privacy, and Compliance Baseline

## Purpose

This document defines product controls. It is not legal advice and does not replace review by the brokerage’s Ontario legal, privacy, AML, and regulatory advisors.

## Data classes

### Public

- Published site content.
- Published recruitment postings.
- Published agent profiles.

### Internal

- Administrative configuration.
- Non-sensitive operational notes.
- Aggregated metrics.

### Personal

- Client inquiry contact information.
- Candidate identity and application information.
- Agent information not approved for publication.
- Consent records.
- Review history.
- Borrower contact, date of birth, addresses, application answers, and consent evidence.

### Restricted

- Candidate identity documents.
- Executed agreements.
- Background or suitability evidence.
- Private onboarding records.
- Security events.
- Borrower SIN, financial/property data, free text, identity/supporting documents, encrypted snapshots, legal holds, and access/reveal history.

## Data minimization

The contact-first mortgage inquiry form must not become a mortgage application. The separate Keeper borrower application may collect only the fields approved in `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md`.

Free-text fields must display a warning not to submit:

- SIN.
- banking details;
- credit-card details;
- tax information;
- detailed debt schedules;
- identification documents;
- medical information;
- passwords.

Borrower application fields must not be copied into contact inquiries, URLs, analytics, email, notifications, logs, or audit payloads. Data minimization applies inside the approved full application as well as at the contact boundary.

## Consent

Record service-contact acknowledgement separately from optional marketing consent.

Each consent record should include:

- subject or lead identifier;
- purpose;
- exact or versioned wording;
- privacy-notice version;
- timestamp;
- capture source;
- withdrawal timestamp where applicable.

Borrower submission uses one separately versioned privacy/credit-use consent immediately before submission. It is not marketing consent or an electronic signature. Exact production wording remains a real-data release blocker until owner-approved after appropriate review.

## Candidate privacy

Before submitting an application, candidates must be shown the exact approved disclosure in `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`, versioned immutably as `candidate-privacy-disclosure-2026-07-15-v1`. It covers:

- purpose of collection;
- categories collected;
- who can access;
- expected retention approach;
- use of service providers;
- contact for privacy questions;
- consequences of not supplying required information.

The server owns the wording version and acknowledgement timestamp. A wording change creates a new version; it never rewrites the version recorded against an earlier submission.

## Authentication

- Supabase Auth supplies identity; application-database users, roles, relationships, lifecycle, ownership, and resource rules grant access.
- Verified email for candidate portal entry.
- MFA mandatory for brokerage administrators.
- Candidate AAL2 is not required for general portal access, draft saves, or application submission.
- Candidate AAL2 is required for every candidate-document upload and every restricted-document view/download; server-side ownership and lifecycle checks still apply.
- Rate limiting and anti-automation controls.
- Secure password-reset flow.
- Session revocation on suspension/offboarding.
- Borrower draft access uses an accountless exact-draft capability in a secure host-only cookie; the digest, origin, CSRF, expiry, revision, and lifecycle are validated server-side.
- Assigned agents and administrators require active local authorization plus AAL2 for borrower application, document, legal-hold, and SIN-reveal operations.

## Authorization

- Deny by default.
- Server-side checks.
- Role and resource checks.
- Candidate can access only their own record.
- Internal notes never returned in candidate schemas.
- Document access checked on every request.
- Public profile publication is separate from profile editing.
- Public profile publication is server-eligibility checked; the first published slug is permanently locked and reserved after unpublishing.

## Audit events

Record high-risk events including:

- user linked to external identity;
- role granted or revoked;
- candidate application submitted;
- application reopened;
- candidate status changed;
- decision recorded;
- document uploaded, viewed, accepted, rejected, or superseded;
- policy acknowledged;
- onboarding task completed or overridden;
- manual onboarding gate satisfied or reopened, with the exact assignment and bounded evidence metadata;
- Documenso envelope linked, provider-refreshed, or replaced, with the exact assignment and safe status metadata;
- agent profile approved, published, suspended, or archived;
- marketing consent granted or withdrawn;
- export performed;
- admin impersonation, if ever introduced.

Audit records should be append-oriented and restricted from ordinary editing.

Manual gate satisfaction/reopening uses assignment-bound append-oriented
`GateEvidenceEvent` rows with verifier/evidence or reopen reason. E-sign envelope
link, refresh, and replacement emit bounded audit events; replacement also
preserves the predecessor row and links the successor. Dedicated production
audit export and tamper evidence remain Phase 1F work.

## Logging

Never log:

- authentication tokens;
- reset links;
- raw document contents;
- full form payloads;
- private object URLs;
- sensitive free-text values.

Use identifiers, event names, status, request ID, actor ID, and safe error categories.

## File security

- Private storage.
- File-size limits.
- Approved MIME types.
- Extension/MIME mismatch handling.
- Strict type/structure validation and fail-closed ClamAV scanning before private MinIO persistence.
- ClamAV health, signature freshness, failure alerting, and patch operations before pilot approval.
- Download response headers.
- Short-lived access.
- Audit access.
- Quarantine state.
- Deletion and retention controls.

## Retention

Create policy-controlled retention categories before production.

Initial categories:

- unsubmitted lead;
- candidate draft;
- submitted/declined candidate;
- active agent;
- offboarded agent;
- controlled document;
- consent evidence;
- audit event;
- security incident.
- borrower abandoned draft: purge after 30 days of inactivity;
- borrower submitted application and documents: purge seven calendar years after original submission unless an active legal hold excludes the record;
- borrower legal hold: retain until explicit administrator/AAL2 release, then resume the original retention deadline;
- encrypted backups: rolling 30 days unless a later approved operational policy changes it.

The borrower periods above are owner-approved engineering requirements. They do not replace legal/privacy review of the production policy, notices, correction/export process, backup purge, or legal-hold authority. Other record classes still require approved periods.

## Security operations required before production

- Threat model.
- Dependency scanning.
- Secret scanning.
- Code review.
- PostgreSQL, MinIO, and identity-configuration backup/reconstruction with isolated restore tests.
- Incident response, stop criteria, escalation, rollback, and return-to-service procedures.
- Secrets, credentials, role, access, MFA, revocation, and offboarding review.
- Production Supabase Auth and transactional-email configuration, including invitation, recovery, refresh-token revocation, and offboarding exercises.
- Logging/PII review plus application, database, scanner, object-store, and synthetic monitoring with alert tests.
- MinIO persistence, retention, bucket-policy, signed-download, backup, restore, and orphan-reconciliation review.
- ClamAV signature-freshness monitoring, health alerts, failure exercises, and fail-closed verification.
- Firewall, service-binding, network-exposure, and Linux host review.
- Retention, deletion, correction, data/audit export, legal-hold, and end-of-pilot procedures.
- Vulnerability remediation process.
- Privacy notice and data-processing register.
- Vendor and subprocessor register.
- Privacy, legal, regulatory, claims, complaints, consent, and accessibility review.
- Pilot roster, support ownership, evidence documents, go/no-go criteria, and owner release approval.
- Borrower encryption-key custody, rotation, compromise response, offline recovery, and restored-system overdue-purge exercise.
- Exact borrower-origin DNS/TLS, ingress trust, capability-cookie, CSRF/CORS, rate-limit, request-size, cache, and bot-mitigation review.

## Accessibility

The public site and portal should meet practical WCAG 2.1 AA expectations.

Required:

- semantic structure;
- keyboard operation;
- visible focus;
- labels and instructions;
- error summary;
- color contrast;
- status not communicated by color alone;
- accessible document alternatives where feasible;
- responsive zoom and reflow.

## Regulatory identity and advertising

Brokerage and agent regulatory fields must be configuration-driven and approval-controlled.

No profile is public until approved. Public claims, titles, testimonials, and marketing content require controlled review.
