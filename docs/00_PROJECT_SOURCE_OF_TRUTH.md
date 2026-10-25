# Keeper Financial — Project Source of Truth

## 1. Product identity

**Product:** Keeper Financial public website and brokerage relationship platform  
**Jurisdiction:** Ontario, Canada  
**Phase:** owner-approved borrower-application expansion, Phase D.2 source contract closure
**Primary users:** Mortgage clients, agent candidates, active mortgage agents, brokerage administrators, compliance reviewers, principal broker

## 2. Product purpose

Keeper Financial requires a professional public web presence and a secure brokerage-controlled platform that manages:

- Mortgage-client entry points.
- Minimal-information contact inquiries.
- Secure borrower mortgage applications and supporting documents.
- Assigned-agent and administrator application review.
- Agent recruitment.
- Candidate applications.
- Candidate review and selection.
- Agent onboarding.
- Controlled policy and document completion.
- Public agent profiles.
- Internal evidence that recruitment, onboarding, approval, and profile publication were controlled.

## 3. Governing product boundary

Keeper Financial will build the public brand, borrower-application intake, recruitment, onboarding, agent administration, and public agent-profile experience.

Keeper is the MVP system of record for borrower application data, SIN, versioned privacy/credit-use consent evidence, supporting documents, lifecycle, attribution, assignment, retention, legal holds, and safe audits. The owner-approved contract is `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md`.

Keeper does not perform credit-bureau connectivity, automated underwriting or approval, lender submission, deal-compliance workflow, commission, payroll, or full client-CRM behavior in this MVP. No Filogix redirect, handoff, export, or API integration is required. A future external integration is a separate decision.

## 4. Phase 1 selected approach

Use a hybrid architecture:

- Brokerage-controlled public website.
- Brokerage-controlled recruitment and onboarding portal.
- Keeper-native secure borrower application at `apply.keeperfinancial.ca` from the same repository and release process.
- Existing external lender-submission operations remain outside Keeper, but the MVP has no Filogix integration or handoff requirement.
- Mortgage-client CRM expansion remains deferred.
- Public agent profile pages are included.
- Independent agent microsites are not included in the MVP.

## 5. Required client entry flow

The public website must provide one clear `Get Started` experience with both paths:

1. **Speak with someone first**
   - Minimal-information contact form.
   - Book-a-call option.
   - Phone option.

2. **Start a secure mortgage application**
   - Enter the Keeper-native application at `https://apply.keeperfinancial.ca`.
   - Use an accountless, capability-bound same-browser draft and submit into the assigned-agent/administrator review workflow.

## 6. Phase 1 technology baseline

Preferred foundation:

- Web: React and TypeScript using an SEO-capable framework.
- API: FastAPI.
- Database: PostgreSQL.
- ORM/migrations: SQLAlchemy and Alembic.
- Identity: owner-hosted Supabase for production (decision 46, `https://hdzmlwhubkecegrhptdd.supabase.co`, ES256 asymmetric JWKS) and the repository-tracked local Supabase CLI/Auth stack for dev/test. The API validates exactly those two identity shapes and fails closed otherwise.
- Authorization authority: application database roles and lifecycle state.
- Object storage: private local S3-compatible MinIO with path-style addressing.
- Malware scanning: local ClamAV `clamd` in Docker Compose; validation and a clean scan are required before private-object persistence.
- Local file storage: test/development fallback only; never the live object store.
- Live/production runtime: Docker Compose on the local Linux host. The local containers are the deployment targets.
- Infrastructure boundary: owner-hosted Supabase is permitted for identity only (decision 46); Cloudflare R2 and external cloud infrastructure keys/services remain excluded.
- Email: transactional provider selected later.
- E-signature: self-hosted Documenso behind a configured server-side adapter; no custom signature system. Provider status refresh is authoritative, uses one configured API origin, rejects redirects, and fails closed.

## 7. Authorization rule

Supabase Auth proves identity only.

A valid authenticated identity does not itself grant access to candidate, agent, or brokerage-administration functionality. The application database must contain an active authorized user relationship and role.

Suspended, rejected, withdrawn, offboarding, and offboarded states must constrain access according to documented policy.

## 8. Sensitive-data boundary

The platform may store the owner-approved borrower application, including primary and co-borrower identity/contact data, SIN, employment/income, property, asset/liability, consent, notes, and open mortgage-supporting document categories including `Other` within the approved application purpose and technical controls, plus the existing lead, recruitment, onboarding, profile, and audit records.

Borrower data is a specially protected class. SIN and application payloads require authenticated application-level encryption; supporting documents require strict type/structure checks, fail-closed ClamAV, encryption, and private MinIO. Borrower capabilities, SIN, application answers, filenames, keys, and document contents must not enter logs, URLs, analytics, notifications, or audit payloads. Internal review requires exact assignment or administrator authority and AAL2.

The platform must not collect or generate credit reports through an integration, lender-submission packages, automated underwriting/approval decisions, deal-compliance records, or unrelated third-party personal data unless separately approved. Product openness for borrower document categories does not remove technical type, size, malware, encryption, authorization, retention, or delivery controls.

## 9. Compliance posture

The platform supports—but does not replace—the brokerage’s legal and regulatory responsibilities.

It must not claim that:

- FSRA status is automatically verified unless an authoritative integration exists.
- FINTRAC compliance is automated merely because fields or checklists exist.
- E-signature validity is guaranteed by a custom checkbox.
- Use of a vendor eliminates the brokerage’s PIPEDA accountability.

## 10. Current implementation and authority checkpoint

The source baseline for this decision is `main` at `5f8a41f34bb3586c59d613848fafc9435a86b50d`, including merged work through PR #9. It contains the accepted public site, contact path, candidate authentication/application/review, onboarding completion, agent activation/profile publication, private candidate documents, local PostgreSQL/MinIO/ClamAV/Supabase topology, and public-content updates. Historical reports retain the exact evidence and limitations of their original checkpoints.

Borrower Phases B, C, D, and E are implemented as bounded source checkpoints
through forward migration `20260726_0015`. Phase D.1 remains the historical API
checkpoint; Phase D.2 closes its approved document, consent, idempotent
submission, generated-contract, and borrower-web contract. Phase F retention
jobs, legal-hold operations, ingress, backup/restore, deployment, monitoring,
and operational evidence remain unimplemented and awaiting separate approval.

On 2026-10-16 the owner and legal review approved the full public-facing copy
review (decision 50). Public pages now follow the plain-language standard
recorded in `docs/06` §Public copy standard: internal and production vocabulary
and duplicated copy were removed, the home page carries approved brokerage value
messaging, and the Privacy Notice was corrected — it previously published
authoring instructions and stated that a complete mortgage application "is
handled through Filogix", contrary to decisions 3 and 38 and `docs/28`. The
notice now discloses the mortgage-application data class, the credit-use
consent, application-level encryption, authorized-access limits, and the
decision-37 retention periods; its effective date is 2026-10-16. The displayed
registration text (`FSCO # 13696`) and the confirmed contact details were
approved to remain exactly as displayed by the owner and legal review on
2026-10-25 (decision 55(f)), closing the verification item this decision raised.
This is a public-content change only: it does not
alter deployment, real-data, retention, migration, or operational-readiness
status. The full before/after change list and the implementation record are in
`docs/38_PUBLIC_COPY_REVIEW.md`.

On 2026-10-21 the owner requested an administration-portal usability pass
(decision 54). The lead queue is now a compact table whose full record expands
per row and which defaults to the `new` status filter, so assigned and closed
inquiries leave the default view; the candidate-review empty state no longer
renders an inert `Send request` button; assignable-agent options and the
applicant account name now distinguish agents that were all labelled
`Candidate`; and the onboarding and agent-profile pages put their lists first
with explicit create/view controls. No API contract, endpoint, migration, model,
lifecycle, authorization, audit, retention, deployment, or real-data status
changes; the affected surfaces and exclusions are recorded in decision 54 and
`docs/06` §Admin portal.

On 2026-10-25 the owner approved a homepage conversion update that also makes
`/apply` the mortgage readiness review surface (decision 55) — no new
`/mortgage-readiness/` route was created. The home page hero keeps its approved
headline, offers `Book a Mortgage Readiness Review` and `Start Your
Application` as its two paths (both to `/apply`, at the `#readiness` and
`#application` anchors), and the goal section and closing band link the same
way. `/apply` now opens with the readiness framing, a six-goal selector that
fills the request form's mortgage goal, and a "What to expect" section, while
the secure-application card is unchanged in destination. The only data change is
one optional `source` label on `LeadInquiryCreate` (`website_apply` |
`website_readiness`), stored on the existing column and on the consent records,
with no migration. Analytics (Part C of the brief) was deliberately not
implemented — no analytics of any kind is installed and the Privacy Notice
states the public site uses none — and no scheduler was configured. No
lifecycle, authorization, audit, retention, deployment, or real-data status
changes.

On 2026-10-25 the agent-profile editor replaced its pasted photo URL with a
Keeper-served upload (decision 56). An administrator selects one JPEG or PNG (5
MiB cap); the API validates and malware-scans it, writes the bytes to the
existing private MinIO bucket under `public/agent-photos/`, and returns a stable
HTTPS URL served only by the public read route
`GET /api/v1/agent-photos/{photo_id}`. The bucket stays private and public
object URLs remain prohibited — no anonymous access, bucket policy, CDN, second
bucket, migration, model, lifecycle, role, retention, data-class, deployment, or
real-data status changes. New settings are `PUBLIC_SITE_BASE_URL` and
`AGENT_PHOTO_MAX_BYTES`; the public read route is a deliberately narrow,
recorded exception to the "no public object route" threat-model control that
covers approved agent marketing photos only.

On 2026-07-24 the owner authorized normal branch, commit, push, pull-request, and merge operations for the approved borrower work. That authority does not authorize deployment, shared-database production mutation, real-borrower data, live secrets, external-service changes, force-push/history rewriting, destructive data operations, or legal/privacy/regulatory approval.

On 2026-07-27 the owner approved (a) the assigned-agent full-data retrieval
boundary (Scope B) and (b) stopping the local Supabase stack. Scope B lets the
exact assigned active AAL2 mortgage agent read the unmasked SIN and the full
financial payload (assets, liabilities, subject property, other properties,
additional notes) for their assigned submitted/under-review application, while
the admin/internal `BorrowerInternalProjection` remains masked (display-only
SIN) and withholds those full financial fields. The privacy-boundary decision
and the agent-only authorization model are recorded in
`docs/35_AGENT_FULL_DATA_PRIVACY_APPROVAL.md`; the consolidated implementation
plan is `docs/36_AGENT_RETRIEVAL_MINIMAL_PLAN.md`. Outside the agent web surface
the borrower data stays masked everywhere.

On 2026-07-27 the owner also approved the borrower/mortgage-applicant privacy
and credit-use disclosure wording and immutably versioned it
`borrower-privacy-credit-disclosure-2026-07-27-v1`. This resolves the former
"exact production wording remains an owner/legal-content prerequisite" gap for
the borrower MVP. The approved text is recorded verbatim in `docs/28` §6 and is
deliberately distinct from the Phase 1C candidate privacy disclosure
(`docs/19`) — recruitment/candidate scope and borrower scope coexist. Real-data
borrower submission remained disabled until the separate owner release/deploy
approval and secure-deployment evidence existed; approved wording alone did not
enable submission. On 2026-07-30 the owner provided explicit deploy/release and
"deploy now" approval for the self-hosted Keeper replacement on the target
Ubuntu host `inspiron`. That approval removes the missing-owner-approval gate
for deployment and release execution, but it does not weaken the required secure
deployment evidence, runtime feature gates, consent-catalog approval marker,
backup/restore, firewall, TLS, private MinIO, fail-closed ClamAV, local Supabase
Auth boundary, AAL2, logging minimization, non-destructive WordPress preservation
during side-by-side testing, or separate approval for destructive rollback/restore
or credential/external-service changes. The owner directed the candidate disclosure not be reused
verbatim for borrowers; the adopted text was corrected to match the approved
borrower collection set (SIN and financial data are collected and specially
protected; résumé, cover letter, education/training, referral source, applicant
statements, and availability are not collected from borrowers).

## 11. Phase 1 release condition

Phase 1 is releasable only when:

- Public website routes are production-ready.
- Both client entry paths work.
- The Keeper-native borrower application and document path passes its approved authorization, encryption, consent, lifecycle, retention, legal-hold, malware, browser, and operational gates.
- Candidate identity and role controls are tested.
- Candidate application and review workflow works.
- Onboarding tasks and controlled documents work.
- Agent-profile approval and publication work.
- Candidate documents are private.
- Audit events are generated for high-risk actions.
- Environment validation fails closed.
- Required privacy, complaints, accessibility, and consent pages exist. The public accessibility statement (`apps/web/app/(public)/accessibility/page.tsx`) is approved site content and is not a standalone release blocker (a formal specialist accessibility review remains a deferred production item per `docs/26`).
- The owner provided explicit "deploy now" approval on 2026-07-30 for the self-hosted Keeper replacement on target host `inspiron`. The borrower privacy/credit-use disclosure wording was approved 2026-07-27 (`borrower-privacy-credit-disclosure-2026-07-27-v1`); the minimal operational-readiness baseline (`docs/37`) and accessibility incorporation are complete. Pilot go/no-go criteria are not a gate before deployment execution. Real-borrower submission still requires the deployed runtime evidence and the implemented release controls: `BORROWER_APPLICATION_ENABLED=true`, `BORROWER_REAL_DATA_ENABLED=true`, and the active consent-catalog row's server-owned `real_data_approved=true` marker for the exact approved consent version/digest.

## 12. Change-control rule

Any approved change to scope, architecture, security boundaries, lifecycle states, systems of record, or compliance assumptions must update this file and all affected supporting documents in the same branch.

The deployment and borrower-application decisions above supersede contradictory external-application, prohibited-borrower-data, hosted-service, and undecided-hosting language in historical implementation reports and bootstrap prompts; those files remain historical evidence rather than current instructions.
On 2026-07-31 the owner additionally approved retaining the target host's existing
Nginx/Let's Encrypt ingress rather than replacing it with Caddy. The repository-managed
Nginx template and runbook are authoritative for the target host; Nginx is the sole
public ingress on `80/443`, while Keeper services remain loopback/private.

On 2026-10-13 the owner moved production identity to the owner-hosted Supabase
project `https://hdzmlwhubkecegrhptdd.supabase.co` (decision 46) because the
target `inspiron` host cannot run the local Supabase CLI container stack
(SIGILL / exit 132). This supersedes the hosted-Supabase prohibition in decision
14 and the "local Supabase Auth boundary" clause of decision 44 and of the
2026-07-30 paragraph above. Identity scope only: application data, object bytes,
and malware decisions stay on the local Compose PostgreSQL/MinIO/ClamAV services;
Supabase Storage stays disabled; borrowers remain accountless; and dev/test
retains the local Supabase CLI stack. Decisions 47 and 48 record the pinned
legacy MinIO image and the accepted below-baseline CPU risk.

On 2026-10-14 the owner approved a revised, commercially proportionate Phase F
readiness scope (decision 49): implement the P0 production security controls now —
production fail-closed configuration validation, encrypted PostgreSQL plus coordinated
PostgreSQL/MinIO backups with restore-time deletion reconciliation as a defined safety
gate, and basic cron/script monitoring — while deferring the automated borrower purge
scheduler, a legal-hold API/management UI, candidate-document lifecycle automation, and a
global log-redaction framework. The borrower retention model is recorded as an explicit
unresolved owner decision: decision 37's seven-year submitted-record and 30-day-draft
retention remains authoritative and unchanged; the proposed minimal-retention
transfer-then-delete model is not adopted because it presumes a Filogix/origination
handoff excluded by the approved MVP boundary, and it requires Ontario
compliance/privacy validation before any purge/deletion code. Real-borrower submission
remains gated by the runtime release controls until the retention model is resolved and a
real restore drill succeeds.
