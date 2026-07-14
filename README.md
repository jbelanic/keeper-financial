# Keeper Financial — Phase 1 Baseline Pack

This pack defines the initial product, architecture, security, privacy, delivery, and Codex operating baseline for a fresh Keeper Financial project.

## Phase 1 outcome

Launch a production-ready foundation for:

1. A professional public brokerage website.
2. A single `Get Started` experience with:
   - a minimal-information contact path; and
   - a secure redirect to the selected mortgage application vendor.
3. Public mortgage-agent recruitment pages and postings.
4. Candidate account creation and online applications.
5. Brokerage review and selection workflows.
6. Selected-candidate onboarding with controlled documents, acknowledgements, completion tracking, and administrative approval.
7. Brokerage-controlled public agent profile pages.
8. An architecture that can integrate with Filogix, Scarlett, or another mortgage platform without storing full borrower mortgage applications.

## Explicitly out of scope

Phase 1 does not build:

- A mortgage origination system.
- A lender-submission system.
- A borrower document vault.
- A credit-bureau integration.
- A mortgage compliance engine.
- A commission or payroll engine.
- A custom e-signature engine.
- A complete mortgage-client CRM.
- Automated FSRA licence verification unless a supported authoritative integration is available.
- Automated provisioning into Filogix, Scarlett, or other third-party systems unless an approved API is available.

## Recommended reading order

1. `docs/00_PROJECT_SOURCE_OF_TRUTH.md`
2. `docs/01_PRODUCT_VISION_AND_SCOPE.md`
3. `docs/02_PHASE_1_MVP_REQUIREMENTS.md`
4. `docs/03_ARCHITECTURE_BASELINE.md`
5. `docs/04_SECURITY_PRIVACY_COMPLIANCE_BASELINE.md`
6. `docs/05_DOMAIN_MODEL_AND_LIFECYCLES.md`
7. `docs/06_UX_UI_IMPLEMENTATION_GUIDE.md`
8. `docs/07_DELIVERY_PLAN.md`
9. `docs/08_ACCEPTANCE_TESTS.md`
10. `docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md`
11. `docs/10_CODEX_WORKING_AGREEMENT.md`
12. `START_HERE_WSL.md`
13. `INITIAL_CODEX_PROMPT.md`

## Governing rule

When documents conflict, `00_PROJECT_SOURCE_OF_TRUTH.md` controls. Any approved scope, architecture, security, privacy, workflow, or status-model change must update the source-of-truth document and the affected supporting documents in the same change.
