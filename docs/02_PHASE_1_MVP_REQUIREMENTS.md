# Phase 1 MVP Requirements

## Priority definitions

- **P0:** required for release.
- **P1:** important but may follow the first controlled release.
- **P2:** explicitly deferred.

## Public website

| ID | Requirement | Priority |
|---|---|---|
| PUB-001 | Present Keeper Financial as a professional Ontario mortgage brokerage. | P0 |
| PUB-002 | Display approved brokerage regulatory identity information in configured site chrome/footer. | P0 |
| PUB-003 | Provide responsive navigation and accessible page structure. | P0 |
| PUB-004 | Provide service pages for purchase, refinance, renewal, first-time buyers, and investment properties. | P0 |
| PUB-005 | Provide an agent directory and public profile pages. | P0 |
| PUB-006 | Prevent unapproved, suspended, or archived profiles from being publicly displayed. | P0 |
| PUB-007 | Provide careers pages and recruitment postings. | P0 |
| PUB-008 | Provide privacy, complaints, accessibility, and contact pages. | P0 |
| PUB-009 | Support search metadata, canonical URLs, social previews, sitemap, and robots controls. | P0 |
| PUB-010 | Provide editable content through an approved controlled mechanism. | P1 |

## Get Started and client inquiry

| ID | Requirement | Priority |
|---|---|---|
| LEAD-001 | `/apply` must clearly offer contact-first and Keeper-native full-application paths. | P0 |
| LEAD-002 | Contact-first form collects only approved minimal fields. | P0 |
| LEAD-003 | Form warns users not to submit sensitive financial information. | P0 |
| LEAD-004 | Service-contact acknowledgement is required. | P0 |
| LEAD-005 | Marketing consent is separate, optional, unchecked by default, and versioned. | P0 |
| LEAD-006 | Capture source and optional preferred-agent attribution without sensitive URL values. | P0 |
| LEAD-007 | Route full applications only to the exact Keeper-owned `apply.keeperfinancial.ca` origin. | P0 |
| LEAD-008 | Support phone and book-a-call actions. | P1 |
| LEAD-009 | Provide basic administrative lead visibility or secure forwarding. | P1 |
| LEAD-010 | Keep minimal contact inquiries separate from the purpose-built borrower application; contact fields must still reject mortgage-application data. | P0 |

## Borrower mortgage application

`docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md` is the detailed current specification.

| ID | Requirement | Priority |
| --- | --- | --- |
| BOR-001 | Keeper is the MVP system of record for one primary borrower and at most one co-borrower, their application data, consent evidence, documents, lifecycle, assignment, retention, and audits. | P0 |
| BOR-002 | Borrowers use an accountless, high-entropy, exact-draft capability in a secure host-only cookie; no borrower account, MFA, cross-device resume, emailed resume link, or post-submission portal is included. | P0 |
| BOR-003 | The typed server-owned schema collects the approved mortgage, applicant, SIN, employment/income, property, asset/liability, and note fields and rejects unknown fields. | P0 |
| BOR-004 | SIN and application payloads use authenticated application-level encryption and never enter logs, URLs, browser persistence, analytics, email, notifications, or audit payloads. | P0 |
| BOR-005 | Saved SIN is never returned to the borrower; internal display is masked by default and explicit reveal requires the assigned agent or administrator at AAL2 with a safe audit. | P0 |
| BOR-006 | Borrower documents have open business categories including `Other`, but retain strict type/size/structure controls, fail-closed ClamAV, encryption, private MinIO, and authorized delivery. | P0 |
| BOR-007 | Submission requires the exact server-owned privacy/credit-use consent version and creates durable, immutable, idempotent submission evidence before success is returned. | P0 |
| BOR-008 | The application has no marketing consent, electronic signature, credit-bureau call, automated underwriting/approval, lender submission, deal compliance, or Filogix handoff/integration. | P0 |
| BOR-009 | A valid public agent slug is resolved server-side; invalid attribution enters an unassigned queue; access is limited to the exact assigned active agent or administrator at AAL2. | P0 |
| BOR-010 | Abandoned drafts purge after 30 inactive days; submitted records purge seven years after original submission unless an active legal hold excludes them. | P0 |
| BOR-011 | Production borrower submission remains disabled until exact consent wording/version, key custody, DNS/TLS/ingress, backup/restore, monitoring, incident, privacy/security, and release gates are approved and evidenced. | P0 |

## Recruitment postings

| ID | Requirement | Priority |
|---|---|---|
| REC-001 | Admin can create, edit, publish, close, and archive postings. | P0 |
| REC-002 | Public users can browse active postings. | P0 |
| REC-003 | Candidate can start an application from a posting. | P0 |
| REC-004 | Posting source is retained on the candidate application. | P0 |
| REC-005 | Draft and closed postings are not public. | P0 |

## Candidate identity and application

| ID | Requirement | Priority |
|---|---|---|
| CAN-001 | Candidate can register and verify identity. | P0 |
| CAN-002 | Authenticated identity alone does not grant candidate access without an application user record. | P0 |
| CAN-003 | Candidate can save a draft application. | P0 |
| CAN-004 | Candidate can submit once required sections are complete. | P0 |
| CAN-005 | Submitted application becomes controlled; later edits require an explicit reopened or information-request workflow. | P0 |
| CAN-006 | Candidate can upload approved supporting documents privately. | P0 |
| CAN-007 | Candidate can view current status and candidate-visible messages. | P0 |
| CAN-008 | Internal notes are never shown to candidates. | P0 |
| CAN-009 | Candidate can withdraw. | P1 |

## Review and decision

| ID | Requirement | Priority |
|---|---|---|
| REV-001 | Authorized admin can view candidate queue and detail. | P0 |
| REV-002 | Authorized admin can request more information. | P0 |
| REV-003 | Authorized admin can record interview status. | P0 |
| REV-004 | Authorized admin can conditionally select, decline, or mark withdrawn. | P0 |
| REV-005 | Every status change records actor, timestamp, prior state, new state, and reason where required. | P0 |
| REV-006 | Invalid lifecycle transitions are rejected by backend policy. | P0 |
| REV-007 | Principal-broker approval is separately identifiable where required. | P1 |

## Onboarding

| ID | Requirement | Priority |
|---|---|---|
| ONB-001 | Admin can define reusable onboarding plans and tasks. | P0 |
| ONB-002 | Selected candidate receives an assigned onboarding plan. | P0 |
| ONB-003 | Tasks support due dates, instructions, completion evidence, reviewer, and status. | P0 |
| ONB-004 | Controlled documents use versions and supersession. | P0 |
| ONB-005 | Candidate can view/download controlled documents only when assigned. | P0 |
| ONB-006 | Policy acknowledgement records document version, user, timestamp, and wording. | P0 |
| ONB-007 | Custom application does not implement cryptographic or legal e-signature. | P0 |
| ONB-008 | Executed copies may be uploaded or linked to an external e-signature envelope. | P0 |
| ONB-009 | Final activation requires configured mandatory gates. | P0 |
| ONB-010 | System provisioning remains a tracked task unless a real integration is approved. | P0 |

## Agent profiles

| ID | Requirement | Priority |
|---|---|---|
| AGT-001 | Admin can create and manage agent profiles. | P0 |
| AGT-002 | Agent may propose profile updates. | P1 |
| AGT-003 | Profile publication requires approval. | P0 |
| AGT-004 | Public page contains configured brokerage and agent regulatory fields. | P0 |
| AGT-005 | Suspended or archived profiles are removed from public navigation and direct public rendering. | P0 |
| AGT-006 | Profile includes a safe agent-specific contact or application attribution path. | P0 |
| AGT-007 | Independent agent-site builder is deferred. | P2 |

## Administration, audit, and operations

| ID | Requirement | Priority |
|---|---|---|
| ADM-001 | Role-based admin routes and actions. | P0 |
| ADM-002 | Structured audit events for authentication-sensitive and high-risk actions. | P0 |
| ADM-003 | Export candidate application and onboarding record. | P1 |
| ADM-004 | Search and filtering of candidates and agents. | P1 |
| ADM-005 | Operational health and database-health checks. | P0 |
| ADM-006 | Safe structured logs. | P0 |
| ADM-007 | Backup and restore process documented before production. | P0 |
