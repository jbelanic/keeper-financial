# Keeper Financial Repository Instructions

## Authority

Before material work, read in order:

1. `docs/00_PROJECT_SOURCE_OF_TRUTH.md`
2. Approved decisions
3. Current phase specification
4. Architecture, security, lifecycle, API, data, and test documents
5. Current implementation
6. Historical reports

Report contradictions. Do not silently select code, memory, a generated artifact, or an old report over approved current requirements.

## Current Implementation Checkpoint

The current implementation base for Borrower Phase D.2 contract closure is
`origin/main` at `2d29a0af97c1198007482154fc270cdac91f5ba6`, including merged borrower
Phases B, C, D.1, E, and the bounded Phase E corrective hardening through
forward migration `20260726_0014`. Historical checkpoint documents remain
evidence of their original branches and review moments.

The owner has explicitly accepted the previously delivered Phase 1 source implementation. On 2026-07-24 the owner additionally authorized repository branch management, commits, pushes, pull requests, and merges for the approved borrower-application work. That Git authority does not itself authorize deployment, live-secret or external-service changes, shared-database mutation, destructive data operations, real-borrower use, or legal/privacy/regulatory approval.

Completed checkpoints include:

- Phase 1D candidate review and onboarding baseline at `6349c16`.
- Phase 1E agent profiles and approved local deployment topology at `384246c`.
- Approved local ClamAV malware-scanning controls at `e9d9f65`.
- Candidate authentication and onboarding completion, including posting-bound provisioning, candidate application workflows, administrator review controls, candidate and administrator TOTP/AAL2 paths, and controlled private-document workflows.
- Genuine local PDF and DOCX upload validation through strict file checks, ClamAV scanning, private MinIO persistence, and metadata refresh.
- SQLAlchemy/Alembic model-schema drift resolution through forward migration `20260718_0007`; the migration chain has one head and `make migrate-check` is clean.
- The owner-accepted administrator/operator refinement, with candidate Alembic head `20260719_0008`, exact-assignment evidence, provider-authoritative Documenso refresh, operator-facing selectors, permanent first-publication slug reservation, and removal of the nonfunctional `/admin/content` placeholder.
- Later accepted onboarding-completion, agent-eligibility/profile, and public-content work advances the current single Alembic head to `20260722_0010`.
- Phase B secure borrower foundation source implementation on `feat/borrower-secure-foundation`: borrower domain models, AES-256-GCM application-level encryption with versioned keyring, capability HMAC authorization, origin/CSRF enforcement, draft lifecycle, no-op save semantics, agent/admin authorization, consent/snapshot/assignment primitives, and forward migration `20260724_0011`. The final validation pass records 504 API tests passing with 11 opt-in skips and one Alembic head. Owner-accepted on 2026-07-24 (owner, via Hermes) as source/validation evidence; not operational or production readiness. Final submission, documents, UI, production consent, deployment, browser evidence, and operational evidence remain pending for later phases.
- Phase D.1 is the historical bounded borrower document-upload/submission API
  checkpoint at migration `20260726_0012`. Phase D.2 completes the already
  approved Phase D source contract with configurable 25 MiB/25 document/250 MiB
  maxima, category metadata, capability draft list/removal, server consent,
  caller-idempotent locked submission, and the borrower web journey through
  forward migration `20260726_0015`. This is not Phase F or readiness approval.

On 2026-07-20, the owner authorized a narrowly bounded minimum end-to-end onboarding-completion implementation: one configured owner-maintained Documenso ICA template issued to the exact application-linked authoritative user with validated template/external-ID/recipient/envelope provenance; provider-authoritative administrator refresh; and one explicit administrator/AAL2 completion operation that revalidates an activatable submitted application and nonterminal relationship, then atomically and idempotently completes the exact assignment, activates its exact application and candidate relationship, retains the candidate role, grants the existing `agent` role once, and appends safe history/audit evidence. Manual/recovery envelope links cannot satisfy readiness or completion; failed or recovery-only current envelopes may be superseded only after a new Keeper issuance succeeds. This authority excludes webhooks, agreement authoring/storage, arbitrary templates/recipients/content, automatic agent-profile creation/publication, deployment, shared-database mutation, external-service configuration changes, and broad Phase 1F work.

The bounded onboarding-completion source has since been merged. Historical branch-publication restrictions no longer describe the current repository, but deployment, shared-database mutation, real-person use, credential/external-service changes, destructive operations, and production approval still require their own current authority and evidence.

Do not describe Phase 1D, Phase 1E, candidate-authentication remediation, document-upload remediation, or general Alembic drift as the next implementation phase.

Do not remove or replace the approved MinIO and ClamAV architecture.

The continuation host is Linux Mint. The approved local stack includes:

- application PostgreSQL;
- FastAPI backend;
- Next.js frontend;
- Supabase Auth;
- local mail capture;
- MinIO private object storage;
- ClamAV malware scanning.

Supabase Studio is permitted only for local operator use. Supabase Storage and its S3 protocol remain disabled and are not application storage.

Supabase Auth proves identity only. It does not by itself grant application access. Application-database relationships, roles, lifecycle state, ownership, and resource-specific authorization remain authoritative.

Generic sign-in remains non-provisioning. Posting-bound registration or sign-in may create or reuse the approved candidate application records only through the dedicated provisioning boundary.

The local administrator-linking command is permitted only in `APP_ENV=local` for a seeded placeholder application identity. It must never:

- infer or grant an administrator role;
- link automatically by matching email;
- create a Supabase Auth user;
- use service-role credentials;
- overwrite a genuine non-placeholder provider subject.

Activation gates, `activation_ready`, and the separately approved explicit onboarding-completion operation are implemented. Readiness alone must never activate an agent, and no alternate or automatic activation path is authorized.

## Owner-approved borrower-application boundary

On 2026-07-24 the owner approved Keeper becoming the MVP system of record for borrower mortgage-application intake and supporting documents. `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md` is the current phase specification and `docs/migrations/mortgage-app-import-manifest.md` records legacy provenance.

The approved boundary includes one primary borrower and at most one co-borrower, SIN, financial/application data, supporting documents without narrow business-category restrictions, versioned privacy/credit-use consent, assigned-agent/administrator review, seven-year submitted-record retention, legal holds, and secure self-hosted operation. It requires accountless capability-bound drafts, application-level encryption, private MinIO, fail-closed ClamAV, server-side assignment authorization, AAL2 for internal access, safe audit evidence, and exact-host/TLS/browser controls.

No Filogix redirect, handoff, export, or API integration is part of the MVP. Borrower accounts/MFA, electronic signatures, marketing consent, credit-bureau connectivity, automated underwriting, lender submission, deal compliance, full CRM, commission, and payroll remain excluded. The owner approved the borrower/mortgage-applicant privacy and credit-use disclosure wording on 2026-07-27 (`borrower-privacy-credit-disclosure-2026-07-27-v1`, recorded in `docs/28` §6); the prior "exact production wording remains a prerequisite" gap is resolved for the borrower MVP, but real-data borrower submission and production deployment remain separate explicit owner approvals under the Phase 1F readiness plan.

The bounded source implementation is not by itself evidence that the full
borrower lifecycle is complete or ready for real data. Continue only through
the approved phased plan, dedicated branches/worktrees, migrations and
generated contracts where applicable, adversarial authorization/security
tests, genuine synthetic browser evidence, and explicit operational
acceptance.

Phase 1F readiness work must distinguish:

- confirmed completed implementation;
- operational evidence still required;
- owner decisions;
- privacy, legal, regulatory, claims, and accessibility review;
- pilot go/no-go criteria;
- deferred production work.

## Historical reports

Preserve dated implementation, readiness, migration, and evidence reports as records of their original branches and review moments. Correct stale current-state language in living documents; do not rewrite a historical conclusion merely because later work was merged. Add a clearly dated post-merge note to a historical report only when necessary to prevent it from being mistaken for current status.

## Product boundaries

- Build and maintain the public site, lead/contact-first path, Keeper-native borrower application/document intake, assigned-agent and administrator review, recruitment, candidate application and review, onboarding, controlled-document, administration, and approved agent-profile experience.
- Keep lender submission, underwriting decisions/automation, deal-compliance workflow, credit-bureau connectivity, commissions, payroll, and full CRM behavior outside Keeper unless separately approved.
- Do not introduce a new sensitive-data class beyond the approved borrower requirements, custom legal e-signature platform, automated regulatory/identity verification claim, lender-network claim, approval claim, or compensation claim without an approved decision.
- Do not weaken server-side authorization, MFA, privacy boundaries, malware scanning, private-object storage, lifecycle controls, audit evidence, retention controls, or fail-closed behavior.

## Production and controlled-pilot readiness boundary

Before production or controlled-pilot execution, complete the approved readiness plan and obtain the required evidence and owner approvals covering at minimum:

- Supabase Studio local-only enforcement;
- confirmation that Supabase Storage remains disabled;
- MinIO persistence, backup, retention, and isolated restore testing;
- ClamAV signature freshness, health monitoring, alerting, and fail-closed operation;
- firewall, service binding, and network exposure;
- secrets, credentials, MFA, roles, access review, revocation, and offboarding;
- borrower encryption-key custody, rotation, compromise recovery, backup, and restore;
- exact borrower-origin DNS/TLS, ingress trust, cookies, CSRF/CORS, abuse controls, and request limits;
- borrower draft/submission retention, legal holds, purge, correction, export, and incident handling;
- production authentication and email configuration;
- logging and PII safety;
- incident response, stop criteria, rollback, and return-to-service;
- monitoring, synthetic checks, escalation ownership, and alert testing;
- privacy, legal, regulatory, claims, consent-copy, and accessibility review;
- deployment architecture and environment guardrails;
- database migration, backup, rollback, and isolated restore boundaries;
- pilot roster, support ownership, eligibility, go/no-go criteria, and evidence documents.

Do not enable real-borrower submission or deploy the borrower workflow until the applicable implementation, evidence requirements, owner decisions, exact consent copy, scope, and acceptance criteria are approved.

## Implementation discipline

Before editing:

- inspect Git branch, HEAD, status, remotes, relevant code, migrations, generated contracts, tests, and documents;
- confirm the current phase and authoritative checkpoint;
- state scope, exclusions, assumptions, acceptance criteria, security/privacy constraints, and validation plan;
- stop on a material missing product, lifecycle, legal, privacy, security, or operational decision.

During editing:

- use the smallest coherent change;
- preserve unrelated behavior and issued migrations;
- use forward migrations rather than rewriting issued history;
- enforce authentication and authorization server-side;
- add or update tests first where practical;
- keep schemas, OpenAPI, generated contracts, migrations, and frontend types aligned;
- preserve exact posting-specific and application-specific targeting;
- do not weaken fail-closed guards, logging minimization, audit controls, retention controls, or privacy boundaries;
- update all affected current documents in the same branch;
- preserve historical reports unless they are explicitly identified as living documents.

After editing:

- run the applicable formatter, lint, type, test, migration, contract-generation, build, container, health, and security checks;
- run `make migrate-check` when model or schema metadata may be affected;
- confirm one Alembic head and the expected current revision;
- review the final diff against every acceptance criterion;
- report files changed, exact commands and results, documentation updates, residual risks, and exact `git status`.

## Git and operations

The owner authorized standard branch, commit, push, pull-request, and merge operations for the approved borrower-application work on 2026-07-24. This does not authorize force-push, history rewriting, branch deletion, deployment, shared-database mutation, credential rotation, external-service changes, or destructive data operations unless separately and explicitly approved.

Use one dedicated branch or worktree per implementation phase. Do not allow concurrent writers to modify the same files, branch, or worktree.

Only one writer should use the primary checkout at a time. In particular, do not allow:

- `keeper-architect` and `keeper-marketing` to edit simultaneously;
- Hermes and Codex to edit simultaneously;
- two Codex sessions to use the same branch and worktree.

Use Git worktrees when genuine parallel work is required.

## Hermes roles

- `keeper-architect` owns source-of-truth stewardship, architecture and security analysis, phase planning, acceptance criteria, Codex prompt consolidation, implementation review, and readiness-gap analysis.
- `keeper-marketing` owns controlled public content, recruitment and onboarding copy, conversion journeys, SEO, and claim dependencies. It does not own application architecture, security decisions, schema design, production code, or regulatory conclusions.
- Hermes memory and skills are advisory only and never override repository evidence or approved owner decisions.
- Hermes profiles must not silently initiate implementation, modify repository files, create memory, create skills, delegate work, or invoke Codex when operating under a read-only validation request.

## Codex prompt rule

Use one consolidated implementation prompt per approved phase.

The prompt must include:

- mandatory documents and current evidence;
- exact branch and checkpoint;
- scope and exclusions;
- requirements and acceptance criteria;
- security, privacy, legal, lifecycle, and operational constraints;
- migration and generated-contract requirements;
- tests and genuine-browser validation where applicable;
- documentation updates;
- validation commands;
- Git restrictions;
- stop conditions;
- completion-report format.

Codex is the bounded implementation engine. It implements only the approved consolidated phase prompt, reports contradictions and blockers, preserves owner decisions and repository boundaries, and does not independently expand product scope, architecture, data classes, external integrations, or deployment authority.
