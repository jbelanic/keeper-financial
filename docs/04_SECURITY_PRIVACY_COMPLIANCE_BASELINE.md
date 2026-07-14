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

### Restricted

- Candidate identity documents.
- Executed agreements.
- Background or suitability evidence.
- Private onboarding records.
- Security events.

## Data minimization

The contact-first mortgage inquiry form must not become a mortgage application.

Free-text fields must display a warning not to submit:

- SIN.
- banking details;
- credit-card details;
- tax information;
- detailed debt schedules;
- identification documents;
- medical information;
- passwords.

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

## Candidate privacy

Before submitting an application, candidates must be shown:

- purpose of collection;
- categories collected;
- who can access;
- expected retention approach;
- use of service providers;
- contact for privacy questions;
- consequences of not supplying required information.

## Authentication

- Managed identity provider.
- Verified email for candidate portal entry.
- MFA mandatory for brokerage administrators.
- MFA strongly encouraged or required for candidates handling restricted documents.
- Rate limiting and anti-automation controls.
- Secure password-reset flow.
- Session revocation on suspension/offboarding.

## Authorization

- Deny by default.
- Server-side checks.
- Role and resource checks.
- Candidate can access only their own record.
- Internal notes never returned in candidate schemas.
- Document access checked on every request.
- Public profile publication is separate from profile editing.

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
- agent profile approved, published, suspended, or archived;
- marketing consent granted or withdrawn;
- export performed;
- admin impersonation, if ever introduced.

Audit records should be append-oriented and restricted from ordinary editing.

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
- Malware scanning before acceptance in production.
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

Do not hard-code final legal retention periods without approved policy.

## Security operations required before production

- Threat model.
- Dependency scanning.
- Secret scanning.
- Code review.
- Backup and isolated restore test.
- Incident response plan.
- Access review.
- MFA confirmation.
- Logging review.
- Object-storage review.
- Vulnerability remediation process.
- Privacy notice and data-processing register.
- Vendor and subprocessor register.

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
