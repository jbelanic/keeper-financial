# Test Strategy

## Phase 0 layers

- API unit/service tests: lifecycle maps, reason rules, profile approval, redirect validation, environment fail-closed behavior.
- API boundary tests: anonymous/identity-only/candidate/admin authorization, inactive and suspended/offboarded denial, minimal lead validation and consent separation, direct-peer rate limiting, forwarded-header spoof resistance, automation-trap rejection, document isolation, API/database health distinction.
- Web tests: required public/protected route inventory, portal authorization request behavior, contact-form privacy warning and separate marketing checkbox.
- Static checks: Ruff, mypy, ESLint, TypeScript, Prettier, Python compilation.
- Integration checks: Alembic upgrade/check on PostgreSQL, Next production build, Docker Compose configuration.

## Security regression expectations

Every protected route must add tests for anonymous, authenticated-but-unmapped, wrong-role, inactive/lifecycle-denied, and authorized access. Every candidate-owned resource must include cross-candidate identifier tests. New status operations must include invalid transitions and required-reason tests. New public data queries must prove unpublished states are absent.

Do not replace database-backed authorization tests with UI visibility tests. Hiding navigation is not authorization. Do not weaken environment validators or service transition rules to simplify fixtures.

## Before production

Add real Supabase JWT/JWKS tests, R2 bucket-policy and signed-URL tests, malware-scanner tests, multi-replica/edge abuse-control tests, browser accessibility automation plus manual WCAG review, continuous dependency/secret scanning, backup/restore exercises, and deployment health/rollback tests.
