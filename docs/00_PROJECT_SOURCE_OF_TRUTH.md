# Keeper Financial — Project Source of Truth

## 1. Product identity

**Product:** Keeper Financial public website and brokerage relationship platform  
**Jurisdiction:** Ontario, Canada  
**Phase:** Phase 1 baseline  
**Primary users:** Mortgage clients, agent candidates, active mortgage agents, brokerage administrators, compliance reviewers, principal broker

## 2. Product purpose

Keeper Financial requires a professional public web presence and a secure brokerage-controlled platform that manages:

- Mortgage-client entry points.
- Minimal-information contact inquiries.
- Agent recruitment.
- Candidate applications.
- Candidate review and selection.
- Agent onboarding.
- Controlled policy and document completion.
- Public agent profiles.
- Internal evidence that recruitment, onboarding, approval, and profile publication were controlled.

## 3. Governing product boundary

Keeper Financial will build the public brand, recruitment, onboarding, agent administration, and public agent-profile experience.

Keeper Financial will buy or use an established mortgage platform for:

- Full borrower mortgage applications.
- Borrower financial data.
- Borrower document collection.
- Credit consent and bureau connectivity.
- Mortgage underwriting records.
- Lender submissions.
- Deal compliance.
- Commission and payroll capabilities where applicable.

## 4. Phase 1 selected approach

Use a hybrid architecture:

- Brokerage-controlled public website.
- Brokerage-controlled recruitment and onboarding portal.
- External secure mortgage application.
- Existing Filogix lender-submission workflow remains in place unless a later approved decision changes it.
- Mortgage-client CRM expansion is deferred until the existing Filogix CRM capability is assessed in operation.
- Public agent profile pages are included.
- Independent agent microsites are not included in the MVP.

## 5. Required client entry flow

The public website must provide one clear `Get Started` experience with both paths:

1. **Speak with someone first**
   - Minimal-information contact form.
   - Book-a-call option.
   - Phone option.

2. **Start a secure mortgage application**
   - Redirect to the configured external mortgage-application provider.
   - No recreation or embedding of a custom mortgage application unless separately approved.

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

The custom platform must not collect or store full mortgage application data.

It may store:

- Minimal client lead/contact data.
- Agent candidate application information.
- Recruitment and onboarding documents.
- Policy acknowledgements.
- Agent profile and licensing information.
- Administrative review and audit records.

It must not store borrower:

- SIN.
- Credit reports.
- Bank statements.
- Tax returns.
- Detailed assets and liabilities.
- Government identification for mortgage underwriting.
- Lender submission packages.
- Mortgage underwriting notes.

## 9. Compliance posture

The platform supports—but does not replace—the brokerage’s legal and regulatory responsibilities.

It must not claim that:

- FSRA status is automatically verified unless an authoritative integration exists.
- FINTRAC compliance is automated merely because fields or checklists exist.
- E-signature validity is guaranteed by a custom checkbox.
- Use of a vendor eliminates the brokerage’s PIPEDA accountability.

## 10. Current implementation checkpoint

The current merged baseline is `main` at `3331519de482c2bd062b7b7e10e067f06c42f9a3`; it includes the implementation merge at `b906027` and:

- Phase 1D review/onboarding and Phase 1E agent-profile/local-topology baselines.
- Posting-bound candidate provisioning while generic sign-in remains non-provisioning.
- Candidate application, application-specific review/information-request/decision, onboarding-readiness, candidate/admin TOTP/AAL2, and controlled private-document workflows.
- Strict PDF/DOCX validation, fail-closed ClamAV scanning, private MinIO persistence, and metadata refresh with genuine local synthetic evidence.
- Forward schema reconciliation through `20260718_0007`, one Alembic source head, and a clean recorded `make migrate-check` result without rewriting issued migrations.

Supabase identity alone grants no application access. `activation_ready` is a calculation and does not perform final activation; no final activation operation is currently implemented.

The owner has explicitly accepted the Phase 1 source implementation, including the operator-workflow refinement on `feat/admin-workflow-operator-ux`. That refinement adds editable unused onboarding plans with ordered task authoring; permanent plan immutability after first assignment; exact-assignment manual gate, policy-acknowledgement, and e-sign evidence; Documenso-authoritative status refresh and replacement history; operator-facing exact-application and eligible-agent selectors; permanent published-slug reservation; and removal of the nonfunctional `/admin/content` placeholder. At the verified acceptance-reconciliation state, it remains uncommitted and unmerged on the dedicated branch/worktree and advances the candidate Alembic head to `20260719_0008`.

Source acceptance is not production, controlled-pilot, deployment, final-activation, legal, privacy, regulatory, claims, or accessibility approval. It does not authorize commit, push, pull request, merge, history rewriting, a candidate-to-agent transition, an agent-role grant, shared-database migration, credential or external-service changes, or destructive operations.

The owner subsequently authorized only the Git publication workflow for this accepted source: commit the dedicated branch, integrate the current local `main` without rewriting history, validate the combined source, push it, open and review a GitHub pull request, and merge after successful checks. This separate authorization does not grant deployment, shared-database mutation, production/pilot operation, final activation, lifecycle/role grant, external-service or credential changes, destructive operations, or Phase 1F implementation.

Phase 1F production and controlled-pilot readiness planning is the next gate. The draft plan is `docs/26_PHASE_1F_PRODUCTION_AND_CONTROLLED_PILOT_READINESS_PLAN.md`; its evidence requirements, owner decisions, scope, and acceptance criteria must be approved before Phase 1F implementation. Production deployment, operational evidence, privacy/legal/regulatory/claims/accessibility review, and pilot go/no-go approval remain outstanding. Final activation, candidate-to-agent transition, and agent-role grant remain separately deferred outside Phase 1F. The draft plan's genuine authenticated administrator/operator browser ceremonies are operational evidence blockers for pilot and production, not source-completion blockers, and do not by themselves grant either approval.

## 11. Phase 1 release condition

Phase 1 is releasable only when:

- Public website routes are production-ready.
- Both client entry paths work.
- Candidate identity and role controls are tested.
- Candidate application and review workflow works.
- Onboarding tasks and controlled documents work.
- Agent-profile approval and publication work.
- Candidate documents are private.
- Audit events are generated for high-risk actions.
- Environment validation fails closed.
- Required privacy, complaints, accessibility, and consent pages exist.
- No full mortgage application data is collected.

## 12. Change-control rule

Any approved change to scope, architecture, security boundaries, lifecycle states, systems of record, or compliance assumptions must update this file and all affected supporting documents in the same branch.

The deployment decision above supersedes hosted-service and undecided-hosting language in historical implementation reports and bootstrap prompts; those files remain historical evidence rather than current instructions.
