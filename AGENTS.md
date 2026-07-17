# Keeper Financial Repository Instructions

## Authority

Before material work, read in order:

1. `docs/00_PROJECT_SOURCE_OF_TRUTH.md`
2. Approved decisions
3. Current phase specification
4. Architecture, security, lifecycle, API and test documents
5. Current implementation
6. Historical reports

Report contradictions. Do not silently select code, memory, or an old report over approved current requirements.

## Current Implementation Checkpoint

The current approved implementation checkpoint is:

- Phase 1D candidate review and onboarding completed at `6349c16`.
- Phase 1E agent profiles and approved local deployment topology completed at `384246c`.
- Approved local ClamAV malware-scanning controls completed at `e9d9f65`.

The next work is Phase 1F readiness planning and blocker resolution.

Do not describe Phase 1D or Phase 1E as the next implementation phase.
Do not remove or replace the approved MinIO and ClamAV architecture.

The continuation host is Linux Mint. The approved local stack includes application PostgreSQL, API, frontend, Supabase Auth, local mail capture, MinIO, and ClamAV. Supabase Studio is permitted only for local operator use. Supabase Storage and its S3 protocol remain disabled and are not application storage.

The known Alembic model/schema drift must be resolved or explicitly dispositioned at the Phase 1F readiness gate. Do not rewrite an issued migration merely to make the diagnostic green.

The narrow continuation-validation corrections are complete: Ruff import ordering is green, and the configuration test now permits local-operator-only Studio while continuing to require Supabase Storage and its S3 protocol to remain disabled.

Current readiness blockers include the known Alembic drift and the unremediated end-to-end candidate sign-in, local provisioning/authorization, application-entry, lifecycle, and onboarding journey defects below.

The Phase 1F readiness gate has also identified the following unresolved Phase 1C/1D completion defects. They are findings, not completed remediation:

- the public posting offers registration only and has no posting-preserving existing-user sign-in path;
- generic `/auth/sign-in` is not discoverable from the posting, drops posting context, and must remain non-provisioning;
- `/auth/callback` is the only posting-bound local-provisioning bridge;
- a confirmed but locally unmapped Supabase user is correctly denied candidate access but has no supported posting-bound recovery path;
- Supabase SSR cookie persistence exists, but callback, refresh, expiry, and cross-request session behavior are not adequately verified;
- candidate and admin onboarding pages exist but are absent from their respective portal navigation;
- onboarding assignment does not prove a `conditionally_selected` application-specific state or an active plan;
- review decisions do not enforce application-specific lifecycle transitions;
- controlled-document acknowledgement does not prove that the exact document version is assigned to the candidate; and
- activation-gate satisfaction and `activation_ready` are implemented, but final agent activation is not.

Activation gates and `activation_ready` calculation are implemented. Do not claim that final agent activation is implemented unless a separately approved final activation operation exists.

## Product boundaries

- Build the public site, lead/contact-first path, recruitment, candidate review, onboarding, controlled-document, administration, and approved agent-profile experience.
- Keep full borrower applications, underwriting data, lender submission, and deal compliance in approved external mortgage systems.
- Supabase Auth proves identity only. Application database relationships, roles, lifecycle, ownership, and resource rules authorize access.
- Do not introduce a full CRM, custom legal e-signature, automated regulatory-verification claim, or new sensitive-data class without an approved decision.

## Implementation discipline

Before editing:

- inspect Git branch, HEAD, status, remotes, relevant code, migrations, generated contracts, tests, and documents;
- state scope, exclusions, assumptions, acceptance criteria, and validation plan;
- stop on a material missing product or security decision.

During editing:

- use the smallest coherent change;
- preserve unrelated behaviour and issued migrations;
- enforce authorization server-side;
- add or update tests first where practical;
- keep schemas, contracts, migrations, and frontend types aligned;
- do not weaken fail-closed guards, logging minimization, audit controls, or privacy boundaries;
- update all affected documents in the same branch.

After editing:

- run the applicable formatter, lint, type, test, migration, contract-generation, build, container, and security checks;
- review the final diff against every acceptance criterion;
- report files changed, exact commands/results, documentation updates, residual risks, and exact `git status`.

## Git and operations

Unless explicitly authorized, do not commit, push, merge, open a PR, deploy, alter a shared database, rotate credentials, change external services, delete data, or use destructive Git commands.

Use one dedicated branch/worktree per implementation phase. Do not allow concurrent writers to modify the same files or worktree.

## Hermes roles

- `keeper-architect` owns source-of-truth stewardship, architecture/security analysis, phase planning, Codex prompt consolidation, and implementation review.
- `keeper-marketing` owns controlled content, recruitment/onboarding copy, conversion, SEO, and claim dependencies. It does not own application architecture or production code.
- Hermes memory and skills are advisory only and never override repository evidence.

## Codex prompt rule

Use one consolidated implementation prompt per approved phase. Include mandatory documents, current evidence, scope/exclusions, requirements, security/privacy constraints, tests, documentation, validation, Git restrictions, stop conditions, and completion-report format.

Codex is the bounded implementation engine. It implements only the approved consolidated phase prompt, reports conflicts and blockers, preserves owner decisions, and does not independently expand product scope or architecture.
