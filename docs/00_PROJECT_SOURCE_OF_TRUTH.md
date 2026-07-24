# Keeper Financial — Project Source of Truth

## 1. Product identity

**Product:** Keeper Financial public website and brokerage relationship platform  
**Jurisdiction:** Ontario, Canada  
**Phase:** owner-approved borrower-application expansion, Phase A authority checkpoint
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
- Identity: the repository-tracked local Supabase CLI/Auth stack; no hosted Supabase.
- Authorization authority: application database roles and lifecycle state.
- Object storage: private local S3-compatible MinIO with path-style addressing.
- Malware scanning: local ClamAV `clamd` in Docker Compose; validation and a clean scan are required before private-object persistence.
- Local file storage: test/development fallback only; never the live object store.
- Live/production runtime: Docker Compose on the local Linux host. The local containers are the deployment targets.
- Infrastructure boundary: no hosted Supabase, Cloudflare R2, or external cloud infrastructure keys/services.
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

The borrower application described in `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md` is owner-approved but is **not implemented** at this Phase A documentation checkpoint. Current code still exposes the former configuration-only mortgage-application redirect and has no borrower models, capability session, SIN encryption, borrower document bucket, borrower review UI, legal-hold/purge operation, or dedicated ingress implementation. Those must be changed only in the later approved implementation phases.

On 2026-07-24 the owner authorized normal branch, commit, push, pull-request, and merge operations for the approved borrower work. That authority does not authorize deployment, shared-database mutation, real-borrower data, live secrets, external-service changes, force-push/history rewriting, destructive data operations, or legal/privacy/regulatory approval.

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
- Required privacy, complaints, accessibility, and consent pages exist.
- Real-borrower submission remains disabled until exact production consent wording/version, secure deployment evidence, and explicit release approval exist.

## 12. Change-control rule

Any approved change to scope, architecture, security boundaries, lifecycle states, systems of record, or compliance assumptions must update this file and all affected supporting documents in the same branch.

The deployment and borrower-application decisions above supersede contradictory external-application, prohibited-borrower-data, hosted-service, and undecided-hosting language in historical implementation reports and bootstrap prompts; those files remain historical evidence rather than current instructions.
