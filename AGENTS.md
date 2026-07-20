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

The owner-accepted Phase 1 publication candidate consists of administrator/operator commit `17e1b43` integrated without history rewriting with local `main` content commit `07895c2`; both descend from `3331519`, which includes implementation merge `b906027`. Verify Git before stating whether the publication candidate has merged to remote `main`.

The owner has explicitly accepted the Phase 1 source implementation, including the administrator/operator workflow refinement on `feat/admin-workflow-operator-ux`. The accepted refinement is committed at `17e1b43`; do not describe the combined publication candidate as merged unless Git proves that state.

This is source acceptance only. It does not authorize commit, push, pull request, merge, history rewriting, production or controlled-pilot operation, deployment, shared-database migration, final candidate activation, candidate-to-agent transition, agent-role grant, legal/privacy/regulatory/claims/accessibility approval, credential or external-service changes, destructive operations, or Phase 1F implementation.

On 2026-07-19, the owner separately authorized the accepted branch to be committed, integrated with the current local `main`, fully validated, pushed, reviewed through a GitHub pull request and CI, and merged if the checks pass. That publication authorization does not extend to deployment, shared-database migration, production or controlled-pilot operation, final activation, lifecycle/role grant, credential or external-service changes, destructive operations, or Phase 1F implementation.

Completed checkpoints include:

- Phase 1D candidate review and onboarding baseline at `6349c16`.
- Phase 1E agent profiles and approved local deployment topology at `384246c`.
- Approved local ClamAV malware-scanning controls at `e9d9f65`.
- Candidate authentication and onboarding completion, including posting-bound provisioning, candidate application workflows, administrator review controls, candidate and administrator TOTP/AAL2 paths, and controlled private-document workflows.
- Genuine local PDF and DOCX upload validation through strict file checks, ClamAV scanning, private MinIO persistence, and metadata refresh.
- SQLAlchemy/Alembic model-schema drift resolution through forward migration `20260718_0007`; the migration chain has one head and `make migrate-check` is clean.
- The owner-accepted administrator/operator refinement, with candidate Alembic head `20260719_0008`, exact-assignment evidence, provider-authoritative Documenso refresh, operator-facing selectors, permanent first-publication slug reservation, and removal of the nonfunctional `/admin/content` placeholder.

The next development gate is **Phase 1F production and controlled-pilot readiness planning**. Phase 1F begins with planning and evidence definition, not implementation.

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

Activation gates and `activation_ready` calculation are implemented. Do not claim that final agent activation is implemented unless a separately approved final activation operation exists.

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

- Build and maintain the public site, lead/contact-first path, recruitment, candidate application and review, onboarding, controlled-document, administration, and approved agent-profile experience.
- Keep full borrower applications, underwriting data, lender submission, and deal compliance in approved external mortgage systems.
- Do not introduce a full CRM, custom legal e-signature platform, automated regulatory-verification claim, lender-network claim, approval claim, compensation claim, or new sensitive-data class without an approved decision.
- Do not weaken server-side authorization, MFA, privacy boundaries, malware scanning, private-object storage, lifecycle controls, audit evidence, or fail-closed behavior.

## Phase 1F planning boundary

Before Phase 1F implementation, prepare and obtain approval for a production and controlled-pilot readiness plan covering at minimum:

- Supabase Studio local-only enforcement;
- confirmation that Supabase Storage remains disabled;
- MinIO persistence, backup, retention, and isolated restore testing;
- ClamAV signature freshness, health monitoring, alerting, and fail-closed operation;
- firewall, service binding, and network exposure;
- secrets, credentials, MFA, roles, access review, revocation, and offboarding;
- production authentication and email configuration;
- logging and PII safety;
- retention, deletion, correction, export, and legal hold;
- incident response, stop criteria, rollback, and return-to-service;
- monitoring, synthetic checks, escalation ownership, and alert testing;
- privacy, legal, regulatory, claims, and accessibility review;
- deployment architecture and environment guardrails;
- database migration, backup, rollback, and restore boundaries;
- pilot roster, support ownership, eligibility, go/no-go criteria, and evidence documents.

Do not invoke Codex for Phase 1F implementation until the plan, evidence requirements, owner decisions, scope, and acceptance criteria are approved.

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

Unless explicitly authorized, do not commit, push, merge, open a pull request, deploy, alter a shared database, rotate credentials, change external services, delete data, or use destructive Git commands.

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
