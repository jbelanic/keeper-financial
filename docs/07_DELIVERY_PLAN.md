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

- `/apply` dual path.
- Minimal inquiry form.
- Service-contact acknowledgement.
- Optional marketing consent.
- Agent/source attribution.
- External mortgage-application redirect.
- Administrative lead notification or queue.

## Phase 1C — Recruitment

- Recruitment landing page.
- Posting list/detail.
- Admin posting management.
- Candidate registration.
- Application draft and submission.
- Candidate document upload.
- Candidate status.

## Phase 1D — Review and onboarding

- Admin candidate pipeline.
- Review and information requests.
- Decisions.
- Onboarding templates.
- Candidate task dashboard.
- Controlled documents.
- Acknowledgements.
- Executed-document status/upload.
- Activation gates.

## Phase 1E — Agent profiles

- Profile administration.
- Approval.
- Public directory.
- Public detail.
- Agent-specific attribution.
- Suspension/archive.

## Phase 1F — Production readiness

- Threat model closure.
- Privacy review.
- Accessibility review.
- Backup/restore test.
- Monitoring.
- Incident procedures.
- Vendor due diligence.
- Content and regulatory review.
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
