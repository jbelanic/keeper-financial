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
- Approved local deployment topology implemented with application PostgreSQL,API, frontend, local Supabase Auth, local mail capture, private MinIO, and Docker Compose operations.

## Completed cross-phase control — Local malware scanning

- **Completed at `e9d9f65`.**
- Local ClamAV `clamd` is healthchecked in Compose and required by production configuration.
- Candidate file bytes pass bounded type/structure validation and a clean `INSTREAM` scan before private MinIO persistence.
- Scanner connection, timeout, protocol, and non-clean results fail closed; the scan-only endpoint never persists bytes.

## Phase 1F — Production readiness

- **Next gate: readiness planning and blocker resolution.**
- Threat model closure.
- Privacy review.
- Accessibility review.
- Backup/restore test.
- Monitoring.
- Incident procedures.
- Vendor due diligence.
- Content and regulatory review.
- Resolve or explicitly disposition the known Alembic model/schema drift before launch approval.
- Confirm local-only Studio operations, disabled Supabase Storage/S3 protocol, MinIO bucket policy, ClamAV signature operations, and Linux Mint host hardening.
- Pilot.
- Launch approval.

## 30/60/90/180-day interpretation

### Day 30

- Foundation complete.
- UI mockup translated into tokens and component plan.
- Mortgage application vendor link configured in staging.
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

- Evaluate Filogix CRM usage.
- Measure recruiting funnel and lead conversion.
- Decide whether to add mortgage-specific CRM, open-source CRM, or a limited custom client CRM.
- Consider external e-signature automation.
