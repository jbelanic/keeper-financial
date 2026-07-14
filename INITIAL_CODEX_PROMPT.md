# Consolidated Codex Prompt — Keeper Financial Phase 1 Foundation

You are working in a fresh repository for **Keeper Financial**, a newly established Ontario mortgage brokerage.

Act as a senior product engineer, software architect, security-conscious SaaS developer, and implementation analyst.

## Primary objective

Establish the reviewable technical foundation for Phase 1 without attempting to build the entire product in one pass.

The product boundary is:

1. Public brokerage website.
2. A `Get Started` page offering both:
   - a minimal-information contact-first path; and
   - a secure redirect to an external mortgage-application platform such as Filogix, Scarlett, Finmo, or Velocity.
3. Public mortgage-agent recruitment pages and job/opportunity postings.
4. Candidate registration, authentication, application submission, and application-status visibility.
5. Brokerage-side review, selection, rejection, and request-for-information workflows.
6. Selected-candidate onboarding with controlled documents, policy acknowledgements, completion status, and administrative approval.
7. Brokerage-controlled public agent profile pages.
8. A clean future integration boundary for external mortgage systems and a future client CRM.

The application must **not** become a mortgage origination system.

## Mandatory first step

Read all repository baseline documents before making changes:

- `README.md`
- `START_HERE_WSL.md`
- `docs/00_PROJECT_SOURCE_OF_TRUTH.md`
- `docs/01_PRODUCT_VISION_AND_SCOPE.md`
- `docs/02_PHASE_1_MVP_REQUIREMENTS.md`
- `docs/03_ARCHITECTURE_BASELINE.md`
- `docs/04_SECURITY_PRIVACY_COMPLIANCE_BASELINE.md`
- `docs/05_DOMAIN_MODEL_AND_LIFECYCLES.md`
- `docs/06_UX_UI_IMPLEMENTATION_GUIDE.md`
- `docs/07_DELIVERY_PLAN.md`
- `docs/08_ACCEPTANCE_TESTS.md`
- `docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md`
- `docs/10_CODEX_WORKING_AGREEMENT.md`

Treat `docs/00_PROJECT_SOURCE_OF_TRUTH.md` as authoritative.

## This implementation pass

Complete only **Phase 0 — repository and application foundation**.

Create a maintainable monorepo foundation with:

- A React/TypeScript web application suitable for SEO-capable public pages and authenticated portal routes.
- A FastAPI backend.
- PostgreSQL.
- SQLAlchemy and Alembic.
- Local Docker Compose support.
- Supabase Auth integration boundaries:
  - local Supabase CLI for local development;
  - hosted Supabase Auth for nonlocal identity;
  - backend JWT verification;
  - local application user, role, membership, and lifecycle state as the authorization authority.
- A private document-storage abstraction:
  - local filesystem only in local development;
  - private Cloudflare R2-compatible storage outside local;
  - no public object URLs;
  - signed or proxied authorized retrieval only.
- Typed API contracts or a documented API client generation approach.
- Linting, formatting, type checking, and tests.
- `.env.example` with safe placeholders.
- Environment-tier validation and fail-closed configuration.
- Health endpoints for the API and database.
- Structured logging with no sensitive values.
- A basic audit-event model and service.
- Seed data limited to obviously synthetic local-development data.
- Initial accessible application shells for:
  - public site;
  - candidate portal;
  - brokerage administration portal.

## Initial routes

Create non-final placeholder or foundation routes for:

Public:

- `/`
- `/mortgages`
- `/apply`
- `/agents`
- `/agents/[slug]`
- `/careers`
- `/careers/[slug]`
- `/privacy`
- `/complaints`
- `/accessibility`
- `/contact`

Authenticated candidate:

- `/candidate`
- `/candidate/application`
- `/candidate/onboarding`
- `/candidate/documents`

Authenticated brokerage administration:

- `/admin`
- `/admin/candidates`
- `/admin/onboarding`
- `/admin/agents`
- `/admin/content`

These routes may use foundation-level placeholder content, but navigation, route protection, layout, accessibility, and responsive behavior must be real.

## Required initial data models

Implement only the minimum durable models needed for the foundation:

- `User`
- `UserIdentity`
- `Role`
- `UserRole`
- `Candidate`
- `CandidateApplication`
- `CandidateStatusHistory`
- `RecruitmentPosting`
- `OnboardingPlan`
- `OnboardingTask`
- `CandidateOnboardingTask`
- `ControlledDocument`
- `DocumentVersion`
- `CandidateDocument`
- `PolicyAcknowledgement`
- `AgentProfile`
- `LeadInquiry`
- `ConsentRecord`
- `AuditEvent`

Use UUID primary keys unless a documented reason requires otherwise.

Do not over-model mortgage deals, borrower finances, lender submissions, commission calculations, credit information, or borrower documents.

## Required status foundations

Candidate lifecycle:

- `prospect`
- `application_started`
- `application_submitted`
- `under_review`
- `more_information_required`
- `interview`
- `conditionally_selected`
- `declined`
- `withdrawn`
- `onboarding_in_progress`
- `pending_fsra_authorization`
- `pending_system_provisioning`
- `active`
- `suspended`
- `offboarding`
- `offboarded`

Public agent-profile status:

- `draft`
- `pending_approval`
- `published`
- `suspended`
- `archived`

Document status:

- `required`
- `available`
- `viewed`
- `acknowledged`
- `sent_for_signature`
- `signed`
- `uploaded`
- `accepted`
- `rejected`
- `expired`
- `superseded`

Enforce valid transitions in backend services rather than trusting client-supplied status changes.

## Critical privacy and security boundaries

Do not create fields or forms for:

- SIN.
- Full date of birth for mortgage applicants.
- Credit-card or bank-account information.
- Credit reports.
- Bank statements.
- Tax returns.
- Government identification for borrower mortgage applications.
- Full borrower assets and liabilities.
- Mortgage underwriting documentation.
- Lender submissions.

The contact-first form may collect only:

- name;
- email;
- telephone;
- general mortgage objective;
- preferred contact method;
- optional preferred agent;
- brief free-text message with a warning not to submit sensitive financial information;
- required service-contact acknowledgement;
- separate optional marketing consent.

The `/apply` page must make both paths equally clear:

1. Speak with someone first.
2. Start a secure full application using a configurable external vendor URL.

Do not embed or imitate the vendor mortgage application.

Candidate files may contain personal information. Candidate-document access must be private, authorized, auditable, and unavailable through guessable or public URLs.

## External vendor boundary

Create configuration and adapter interfaces only. Do not fabricate working integrations.

Include configuration placeholders such as:

- `MORTGAGE_APPLICATION_PROVIDER`
- `MORTGAGE_APPLICATION_URL`
- optional agent-specific application-link mapping
- `ESIGN_PROVIDER`
- `CRM_PROVIDER`

Where an integration is not implemented, the application must state that explicitly and fail safely.

## UI requirements

The user has a preferred high-fidelity UI mockup that will be supplied separately.

For this pass:

- Create a design-token foundation.
- Create reusable layout, navigation, form, card, table, status badge, empty state, error state, and loading-state components.
- Use accessible semantic HTML.
- Meet practical WCAG 2.1 AA expectations.
- Ensure keyboard navigation, visible focus, labels, error summaries, and sufficient responsive behavior.
- Do not invent a radically different brand.
- Add a documented location and process for incorporating the approved mockup later.

## Required tests

At minimum, add tests proving:

- Public routes do not require authentication.
- Candidate routes require a candidate account.
- Admin routes require an authorized brokerage-admin role.
- Authenticated identity alone does not grant portal authorization.
- Suspended/offboarded users cannot enter protected areas.
- Candidate status transitions reject invalid changes.
- Agent profiles cannot be published without approval.
- Candidate documents are not publicly addressable.
- Contact-form validation rejects disallowed or excessive input.
- Marketing consent is optional and separately recorded.
- External mortgage application redirects only to an allowed configured HTTPS host.
- Health and database health endpoints behave correctly.
- Environment validation fails closed for unsafe nonlocal configuration.

## Documentation updates

Update or add:

- Root setup and run instructions.
- Local-development instructions.
- Architecture decision record for the selected web framework.
- Environment-variable reference.
- Threat-model summary.
- Initial API route inventory.
- Initial database model inventory.
- Test strategy.
- Known limitations.
- A Phase 0 implementation report.

Do not weaken or silently change the baseline. If a baseline decision is impractical, document the issue and the smallest proposed change. Do not proceed with a contradictory architecture without explicitly recording the decision.

## Engineering constraints

- No secrets in source control.
- No production credentials.
- No public candidate-document bucket.
- No local filesystem storage outside local development.
- No raw authentication tokens in logs.
- No sensitive form payloads in logs.
- No fake compliance claim.
- No assertion that the system itself verifies FSRA status unless an authoritative integration is actually implemented.
- No custom cryptography.
- No custom e-signature implementation.
- No mortgage application data model.
- No large speculative abstraction layer.
- No premature microservices.
- No Kubernetes.
- No analytics trackers on authenticated or sensitive portal screens.

## Deliverable and stopping point

Stop after the foundation is implemented and validated.

At the end, provide:

1. Executive summary.
2. Files and major components created.
3. Architecture decisions made.
4. Database models and migrations created.
5. Routes created.
6. Security and privacy controls implemented.
7. Commands run.
8. Test, lint, type-check, migration, and build results.
9. Known limitations.
10. Open questions requiring owner decisions.
11. Recommended next implementation phase.
12. Exact `git status`.

Do not commit, push, open a pull request, deploy, or change external services unless explicitly instructed.
