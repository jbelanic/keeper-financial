# Test Strategy

## Phase 0 layers

- API unit/service tests: lifecycle maps, reason rules, profile approval, redirect validation, environment fail-closed behavior.
- API boundary tests: anonymous/identity-only/candidate/admin authorization, inactive and suspended/offboarded denial, minimal lead validation and consent separation, direct-peer rate limiting, forwarded-header spoof resistance, automation-trap rejection, document isolation, API/database health distinction.
- Web tests: required public/protected route inventory, portal authorization request behavior, contact-form privacy warning and separate marketing checkbox.
- Static checks: Ruff, mypy, ESLint, TypeScript, Prettier, Python compilation.
- Integration checks: Alembic upgrade/check on PostgreSQL, Next production build, Docker Compose configuration.

## Phase 1A additions

- Anonymous rendering tests cover every finished public page module without invoking an authentication boundary.
- Metadata tests assert unique titles/descriptions, canonical/Open Graph data, all five static mortgage params, public-only sitemap output, and candidate/admin/auth robots exclusions.
- Public-shell tests use accessible role/name queries for desktop navigation, keyboard-native mobile-menu semantics, footer regulatory identity, and real `tel:`/`mailto:` actions.
- Configuration tests prove owner-approved fallback values, exact application/contact facts, disabled optional booking, absent unverified principal broker, and rejection of unsafe optional URLs.
- Publication-boundary tests prove dynamic agent and career slugs return non-public behavior until approved database queries are implemented.
- Source-safety tests guard against mockup-only claims/sample people and assert the explicit narrow-screen/page-overflow CSS controls.
- Existing apply-form minimization/consent tests and API authorization, lifecycle, lead abuse, storage, redirect, and environment tests remain part of the complete pipeline.

Production readiness still requires browser-based automated accessibility and visual-regression coverage at agreed viewports plus manual keyboard, zoom, screen-reader, contrast, and 320 CSS-pixel review.

## Security regression expectations

Every protected route must add tests for anonymous, authenticated-but-unmapped, wrong-role, inactive/lifecycle-denied, and authorized access. Every candidate-owned resource must include cross-candidate identifier tests. New status operations must include invalid transitions and required-reason tests. New public data queries must prove unpublished states are absent.

Do not replace database-backed authorization tests with UI visibility tests. Hiding navigation is not authorization. Do not weaken environment validators or service transition rules to simplify fixtures.

## Before production

Add real Supabase JWT/JWKS tests, R2 bucket-policy and signed-URL tests, malware-scanner tests, multi-replica/edge abuse-control tests, browser accessibility automation plus manual WCAG review, continuous dependency/secret scanning, backup/restore exercises, and deployment health/rollback tests.
