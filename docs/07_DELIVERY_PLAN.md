# Delivery Plan

## Phase 0 — Foundation

Outcome:

- Repository.
- Application shells.
- Authentication and authorization baseline.
- Database and migrations.
- Private storage abstraction.
- Environment validation.
- Design-system foundation.
- Testing and CI foundation.
- Documentation.

## Phase 1A — Public website

- **Engineering implemented on `feature/phase-1a-public-site`; owner/legal approval pending.**
- Approved visual design translated into tokens, components, responsive heroes, cards, trust bands, and CTAs.
- Public navigation, mobile menu, footer, loading/error/empty/not-found behavior.
- Home, mortgage landing, purchase, refinance, renewal, first-time-buyer, investment-property, and How It Works pages.
- About, contact, privacy, complaints, accessibility, careers presentation, agent-directory empty boundary, and visually integrated `/apply`.
- Canonical metadata, Open Graph metadata, sitemap, robots exclusions, and approved-fact structured data.
- Typed repository-controlled content plus validated owner-controlled public configuration.

Phase 1A is not production-approved until the outstanding content/legal, image/font licensing, accessibility, and production-host decisions in `docs/17_PHASE_1A_IMPLEMENTATION_REPORT.md` are resolved.

## Phase 1B — Get Started and lead inquiry

- **Engineering implemented on `feature/phase-1b`; owner/legal/production approval pending.**
- Balanced `/apply` contact-first and controlled full-application paths with adjacent sensitive-data warnings.
- Strict minimal inquiry schema, automation trap, direct-peer bounded limiter, resilient accessible client states, and server-owned consent versions.
- Required service-contact acknowledgement and separate optional marketing consent with safe grant/withdrawal audits.
- Safe query-derived agent attribution accepted only for a published profile; source/capture source remain server-owned `website_apply`.
- Configuration-only external mortgage-application redirect with grammar-checked optional attribution and fail-closed host/URL rules.
- Protected, bounded `/admin/leads` queue with status/page filters only and idempotent admin marketing-consent withdrawal.
- FastAPI-authoritative OpenAPI and generated TypeScript declarations, plus queue-order/filter indexes in migration `20260714_0002`.

Phase 1B does not add notification email, assignment/CRM workflow, export/bulk actions, marketing automation, borrower application data, or production operations. See `docs/18_PHASE_1B_IMPLEMENTATION_REPORT.md`.

These bullets describe the historical Phase 1B implementation. The 2026-07-24 owner decision supersedes the external-application product boundary; the current redirect remains code-to-be-replaced, not the approved target.

## Phase 1C — Recruitment

- **Engineering implemented on `feature/phase-1c`; production/provider/legal operations remain pending.**
- Published-only public posting list/detail and explicit admin create/edit/publish/close/archive lifecycle.
- Supabase registration/verification callback plus narrow, verified, idempotent posting-specific local provisioning.
- Typed approved questionnaire, incomplete draft saves, optimistic revision checks, transactional exactly-once submission, immutable posting provenance, and read-only submitted content.
- Exact server-owned candidate privacy disclosure/version and submission acknowledgement evidence.
- Private résumé/cover-letter upload, signature/MIME/extension/size validation, random keys, quarantine/scan adapter boundary, owner/admin retrieval, and AAL2 enforcement.
- Minimal application-specific candidate status, candidate-owned withdrawal, retained read-only access, and same-posting reapplication as a new attempt.
- Migration `20260715_0003`, generated OpenAPI/TypeScript contracts, accessible public/candidate/admin workflows, and synthetic local fixtures.

At the Phase 1C checkpoint, candidate review/onboarding, agent profiles, and the approved local malware-scanning control were not yet present. Those capabilities are now completed at the Phase 1D, Phase 1E, and ClamAV checkpoints below. Notifications and remaining readiness operations stay in Phase 1F. See `docs/20_PHASE_1C_IMPLEMENTATION_REPORT.md` for the historical Phase 1C evidence.

## Phase 1D — Review and onboarding

- **Completed at `6349c16`.**
- Admin candidate review queue/detail, interview status, information requests, lifecycle decisions, and append-oriented evidence.
- Reusable onboarding plans, candidate assignment, candidate task dashboard/evidence, and administrative task review.
- Controlled-document projections, version-specific policy acknowledgements, external e-signature envelope tracking, and activation gates.
- FastAPI routes, Next.js candidate/admin workflows, migration `20260716_0004`, generated contracts, and focused Phase 1D tests.

## Phase 1E — Agent profiles

- **Completed at `384246c`.**
- Brokerage-admin profile creation, bounded editing, approval/publication lifecycle, and publication evidence.
- Published-only public directory/detail projections, safe configured attribution, and non-public suspension/archive behavior.
- Migration `20260717_0005`, generated contracts, Next.js public/admin workflows, and focused Phase 1E tests.
- Approved local deployment topology implemented with application PostgreSQL, API, frontend, local Supabase Auth, local mail capture, private MinIO, and Docker Compose operations.

## Completed cross-phase control — Local malware scanning

- **Completed at `e9d9f65`.**
- Local ClamAV `clamd` is healthchecked in Compose and required by production configuration.
- Candidate file bytes pass bounded type/structure validation and a clean `INSTREAM` scan before private MinIO persistence.
- Scanner connection, timeout, protocol, and non-clean results fail closed; the scan-only endpoint never persists bytes.

## Completed candidate authentication and onboarding reconciliation

- **Merged to `main` through `b906027`.**
- Published-posting registration and existing-user sign-in converge on the narrow posting-bound provisioning boundary; generic sign-in remains non-provisioning.
- Candidate/admin TOTP/AAL2, exact-application review and information requests, assignment-bound onboarding evidence, and stable no-assignment behavior are implemented and tested.
- Normal office-generated PDF and DOCX files passed genuine local strict validation, ClamAV clean scanning, private MinIO persistence, and metadata refresh.
- Optional owner-operated administrator and second-candidate browser ceremonies remain useful additional release evidence, not uncommitted source-completion blockers.

## Completed schema reconciliation

- Forward migration `20260718_0007` resolves the bounded Phase 1D SQLAlchemy/Alembic drift without rewriting issued migrations.
- The source chain has one head and the recorded post-migration `make migrate-check` result is clean.

## Accepted pre-Phase-1F operator-workflow refinement

- **Phase 1 source implementation is owner-accepted and merged to `main` at `2239441` through PR #4; it combines administrator/operator commit `17e1b43` with approved-content commit `07895c2` without history rewriting.**
- Administrators select exact applications and active plans by human-readable context rather than normal-operation UUID entry.
- Unused plans support ordered task authoring/editing and become immutable on first assignment.
- Manual gate evidence, policy acknowledgements, and e-sign envelopes are exact-assignment records. Only background check, FSRA authorization, and system provisioning are manual; policy acknowledgement and executed agreements are derived.
- Self-hosted Documenso envelope status is refreshed server-side through a fixed-origin, no-redirect adapter. Rejected envelope replacement preserves predecessor history.
- Eligible agents are selected by human-readable identity; readable slug availability is server checked; first publication permanently locks and reserves the slug.
- The nonfunctional content-administration placeholder is removed; repository-controlled content remains authoritative.
- Forward migration `20260719_0008`, generated contracts, focused API/web tests, and isolated PostgreSQL upgrade/check/downgrade/re-upgrade evidence accompany the accepted source state.
- Source acceptance does not authorize commit, push, pull request, merge, history rewriting, deployment, shared-database migration, production/pilot operation, final activation, lifecycle/role transition, credential/external-service changes, or legal/privacy/regulatory/claims/accessibility approval.

## Historical Phase 1F readiness definition

- **Historical status at the Phase 1 checkpoint:** production and controlled-pilot readiness planning, evidence definition, and owner approval were the next gate. The living plan is `docs/26_PHASE_1F_PRODUCTION_AND_CONTROLLED_PILOT_READINESS_PLAN.md`.
- The 2026-07-24 borrower decision does not complete any readiness evidence or authorize deployment/real data; it adds the borrower controls described in the later expansion phases below.
- Threat model closure.
- Privacy, legal, regulatory, claims, consent, complaints, and accessibility review.
- Production Supabase Auth and transactional-email configuration, including invitation, recovery, refresh-token revocation, and offboarding exercises.
- Access, MFA, role, credential, and secrets review.
- PostgreSQL, MinIO, and identity-configuration backup/reconstruction plus isolated restore tests.
- Retention, deletion, correction, data/audit export, legal-hold, and end-of-pilot procedures.
- MinIO bucket/persistence/retention controls and ClamAV signature freshness, monitoring, alerting, and failure exercises.
- Firewall, service binding, network exposure, Linux Mint host hardening, logging/PII safety, monitoring, and synthetic checks.
- Incident escalation, stop criteria, rollback, and return-to-service procedures.
- Migration/rollback/restore operating boundaries that preserve the accepted source chain through `20260719_0008`; applying it to any shared or live database remains separately prohibited pending approval.
- Pilot roster, eligibility, support ownership, evidence documents, go/no-go criteria, and owner launch approval.
- Production deployment requires separate approval. The later merged source contains one explicit bounded administrator/AAL2 onboarding-completion operation; automatic or alternate activation remains prohibited.

## Phase 1G — Approved public/candidate copy (bounded content)

- **The owner-approved content implementation from commit `07895c2` is merged with the administrator/operator refinement through PR #4 at `2239441`.**
- Applied the owner-approved exact public, auth, candidate, and onboarding copy register (C-01–C-17) plus the G renames/removals/internal-text strips.
- Public site (C-01–C-11), `/apply` handoff and unavailable states (C-12), auth/register/sign-in/MFA plain-language copy (C-13), candidate status/list/application instruction/withdrawal (C-14–C-15), and onboarding renames (C-16).
- Stale routes removed: `/admin/content` and the standalone `/candidate/documents`; `ConfirmationDialog` gained optional `confirmLabel`/`cancelLabel`.
- Unresolved `[FW-00x]` factual placeholders omitted/hidden; regulator label left as `FSCO # 13696`; brokerage legal name/address/phone/email taken only from existing config.
- Blocked (DRAFT, separate owner/legal/privacy/regulatory/accessibility approval required): legal/policy pages D-01–D-06, the `/terms` route/link, marketing/privacy-consent version strings, and candidate-disclosure version. External e-signature validity (C-16D) and password-recovery links hidden.
- Remaining dependencies before any publication: FW-001–FW-030 facts (brokerage identity, regulator/licence, principal broker, contact confirmation, agent evidence, opportunity content, compensation, consent/disclosure versions, retention, providers/subprocessors, complaints regulator, accessibility process) and completed D-01–D-06 professional review.

## Borrower application expansion

### Phase A — Authority and requirements

- Synchronize current product, architecture, security, privacy, lifecycle, data, test, readiness, and limitations documents.
- Approve `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md` and preserve legacy provenance in `docs/migrations/mortgage-app-import-manifest.md`.
- No code, migration, generated-contract, deployment, or real-data change.

### Phase B — Secure borrower foundation

- **Source implementation completed on `feat/borrower-secure-foundation`; owner acceptance remains separate.**
- Borrower models, forward migration `20260724_0011`, AES-256-GCM key-ID boundary, keyed accountless capability, typed encrypted drafts, lifecycle and submission-evidence primitives, exact assignment/admin AAL2 authorization, generated OpenAPI/contracts, and adversarial tests.
- No public submit route is mounted. Final submission, borrower document bytes, the Next.js flow, production consent, deployment, and genuine browser/operational evidence remain pending in Phases C–F.

### Phase C — Keeper-native form

- Accessible Next.js flow for one primary and at most one co-borrower; no local storage, typed signature, marketing consent, or external-provider redirect.

### Phase D — Documents and submission

- Strict validation, fail-closed ClamAV, encryption, private borrower MinIO namespace, immutable snapshots, and atomic/idempotent submission.

### Phase E — Agent and administrator review

- Queue, assignment/reassignment, exact assigned-agent isolation, secure rendering/download, masked SIN, and explicit audited AAL2 reveal.

### Phase F — Retention and self-hosted readiness

- Thirty-day draft purge, seven-year submitted retention, legal holds, Caddy exact-host TLS ingress, backup/restore, incident/monitoring controls, and genuine synthetic browser evidence.

### Phase G — Cutover and legacy archive

- Owner-accepted self-hosted cutover followed by non-destructive archival of `jbelanic/MortgageApp`; no deletion or history rewrite.

## 30/60/90/180-day interpretation

### Day 30

- Foundation complete.
- UI mockup translated into tokens and component plan.
- Borrower application authority, threat model, schema, and secure local development boundary approved.
- Public content inventory complete.

### Day 60

- Public website and `/apply` flow functional.
- Recruitment postings and candidate application functional.
- Internal pilot users active.

### Day 90

- Review, onboarding, controlled documents, and profile publication functional.
- Security and accessibility fixes complete.
- Controlled launch.

### Day 180

- Evaluate whether a future Filogix export/import or API integration is technically useful; it is not an MVP dependency.
- Measure recruiting funnel and lead conversion.
- Decide whether to add mortgage-specific CRM, open-source CRM, or a limited custom client CRM.
- Consider external e-signature automation.
