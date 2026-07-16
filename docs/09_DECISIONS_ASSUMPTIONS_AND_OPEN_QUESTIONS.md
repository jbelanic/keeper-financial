# Decisions, Assumptions, and Open Questions

## Approved decisions

1. Use a hybrid model.
2. Do not build a mortgage origination platform.
3. Continue using Filogix for lender submission until a later approved decision.
4. Put both contact-first and full-application paths on one `Get Started` page.
5. Redirect full applications to an external secure provider.
6. Build a custom recruitment and onboarding platform.
7. Build brokerage-controlled public agent profile pages.
8. Defer a full mortgage-client CRM.
9. Assess current Filogix CRM capability before buying or building another CRM.
10. Do not build custom e-signature functionality.
11. Use the exact Phase 1C candidate questionnaire, posting-specific application cardinality, optional résumé/cover-letter categories, privacy disclosure version, and candidate MFA policy in `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`.
12. Permit multiple concurrent posting-specific applications, with no more than one nonterminal application per candidate/posting and immutable new attempts for permitted reapplication.
13. Require candidate AAL2 for document upload and restricted-document access, but not for general portal access, draft saves, or application submission.
14. Deploy the live/production system only as local Docker containers on the Linux host, with the Compose PostgreSQL database, MinIO object storage, and the repository-tracked local Supabase CLI/Auth stack. Do not use hosted Supabase, Cloudflare R2, or external cloud infrastructure credentials/services.

## Initial assumptions requiring confirmation

- Keeper Financial’s public/legal names and currently published regulatory text were supplied for Phase 1A: `Keeper Financial` / `Keeper Financial Inc.` and `FSCO # 13696`. Legal/regulatory approval for production wording remains required.
- Principal broker identity and approved title.
- Exact Filogix product edition.
- Whether Filogix provides the preferred borrower application experience.
- The brokerage-wide secure application URL is approved as `https://apply.keeperfinancial.ca/`. Agent attribution support remains unknown and no agent-specific link is fabricated.
- Preferred booking tool.
- Preferred transactional email provider.
- Preferred e-signature provider.
- Final retention periods.
- Whether active-agent resources remain in this portal after onboarding.
- Who may approve public agent profiles.
- Whether agents may propose their own profile edits.

## UI questions remaining after mockup implementation

- Font licensing and web availability.
- Exact colors and contrast.
- Image licensing.
- Final font licensing and whether an approved vector logo/source photography will replace the accessible text lockup and generated photography-only assets.
- Owner visual approval of the implemented mobile adaptations and 320px reflow.
- Manual WCAG 2.1 AA and content/contrast approval.
- Final legal/privacy/complaints/accessibility wording, formal contacts, escalation steps, and response timelines.

## CRM decision gate

Revisit CRM only after measuring:

- Filogix CRM edition and capabilities.
- Lead response time.
- Lead-entry compliance.
- next-action completion;
- duplicate entry;
- renewal capture;
- agent adoption;
- reporting limitations;
- integration options and cost.

## Change log

Record approved decisions here with date, owner, rationale, and affected documents.

- 2026-07-14 — Implementation decision: selected Next.js App Router for the single React/TypeScript web application, following the preferred architecture baseline. Rationale and consequences are recorded in `docs/adr/0001-nextjs-app-router.md`. No source-of-truth change required.
- 2026-07-14 — Owner-provided Phase 1A public facts: `Keeper Financial` / `Keeper Financial Inc.`, `FSCO # 13696`, London office address, support email, published phone, and `https://apply.keeperfinancial.ca/`. These supersede all mockup sample values and are implemented through validated public configuration.
- 2026-07-14 — Phase 1A content decision: typed repository-controlled content is the approved simplest content mechanism; no CMS or page builder is introduced.
- 2026-07-14 — Phase boundary decision: `/careers` may present the brokerage but exposes no candidate workflow/posting record; `/agents` exposes a finished empty approved-publication boundary; dynamic slugs return non-public behavior until Phases 1C/1E.
- 2026-07-15 — Phase 1C candidate policy approved in `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`: exact questionnaire and validation limits; posting-specific concurrent-application/reapplication rules; optional résumé and cover-letter categories only; immutable privacy disclosure `candidate-privacy-disclosure-2026-07-15-v1`; and candidate AAL2 for uploads and restricted-document access only. No regulatory suitability, licensing, background-check, government-identity, identity-document, or financial questions/documents were introduced.
- 2026-07-16 — Owner deployment decision: the local Linux Docker containers are the live/production targets. Application data uses the Compose PostgreSQL service, objects use private Compose MinIO, and identity uses the existing local Supabase CLI/Auth configuration because the current auth code requires Supabase semantics. Hosted Supabase, Cloudflare R2, and remote cloud infrastructure are excluded.
