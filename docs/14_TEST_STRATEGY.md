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

## Phase 1B additions

- Lead API characterization covers exact public response fields, extra-forbid consent overrides, immutable server versions/source, service/marketing separation, sensitive/control/trap rejection, published versus unpublished profile attribution, and atomic rollback of lead/consent/audit writes.
- Abuse tests cover the exact request boundary, forwarded-header spoof resistance, `Retry-After`, window reopening, existing-client behavior at capacity, and fail-closed admission for new peers.
- Redirect tests cover base and mapped success, slug grammar, unknown mapping, disabled provider, HTTPS, exact host, credentials, query, fragment, and absence of `Location` on failure.
- Both admin lead operations use the full denial matrix: anonymous, unmapped identity, mapped identity-only, inactive, wrong role, candidate, missing required AAL2, and allowed AAL2 admin.
- Queue tests cover no-store, bounded limit, deterministic newest-first order, offset pagination, safe status filtering, necessary response shape, and rejection of PII query keys.
- Withdrawal tests cover marketing-only mutation, preserved grant/service evidence, one-time timestamp/audit, idempotency, safe unknown/absent behavior, actor/request/target metadata, and no duplicate audit.
- Frontend tests cover hidden safe attribution, invalid omission, balanced paths, real phone/conditional booking, backend-only mortgage CTA, duplicate suppression, value preservation, accessible focus/live regions, safe error messages, authenticated no-store queue requests, loading/error/empty/pagination states, text consent states, confirmation, and protected layout/navigation.
- OpenAPI tests pin public versus bearer-protected operations, forbidden consent override properties, success response schemas, and runtime error responses. Generation is run twice and hashes must remain stable.

## Phase 1C additions

- Posting tests cover the full admin denial matrix, bounded plain text/no HTML, lifecycle transition/audit evidence, published-only pagination, direct-slug equivalence, source snapshots, and unmounted premature Phase 1D status operations.
- Provisioning tests cover anonymous/unverified/unpublished, subject/email/role conflict, identity-only denial, atomic narrow grants, retry/idempotency, preserved draft content, same-posting reapplication attempts, and safe audit metadata.
- Application tests cover extra-forbid server fields, exact formats/lengths/repeat limits, ownership, cross-candidate denial, optimistic revisions, immutable provenance, submission requirements/privacy evidence, repeat submission, submitted immutability, minimal status, and application-specific withdrawal.
- Document tests cover candidate AAL2, category/extension/MIME/magic agreement, empty/double-extension/malformed/oversize rejection, random/private storage, clean and quarantined decisions, scanner absence, storage/database failure cleanup, category count, draft deletion, submitted append-only behavior, cross-owner denial, owner/admin retrieval, and safe audits.
- An opt-in isolated PostgreSQL test runs two concurrent application starts and submissions, proving one application, one history, and one submission audit. SQLite remains the fast boundary suite.
- Web tests cover published/error/empty recruitment rendering, Supabase registration and safe callback provisioning bridge, persistent progress, explicit required/optional labels, linked/focused errors, save-before-review, disclosure visibility, duplicate guards, withdrawal focus restoration, AAL2 document announcements/quarantine, and admin lifecycle UI.
- OpenAPI tests pin Phase 1C security declarations, route inventory, internal-field exclusions, and server-owned draft exclusions. Generation is run twice and hashes must remain stable.

Production readiness still requires browser-based automated accessibility and visual-regression coverage at agreed viewports plus manual keyboard, zoom, screen-reader, contrast, and 320 CSS-pixel review.

## Security regression expectations

Every protected route must add tests for anonymous, authenticated-but-unmapped, wrong-role, inactive/lifecycle-denied, and authorized access. Every candidate-owned resource must include cross-candidate identifier tests. New status operations must include invalid transitions and required-reason tests. New public data queries must prove unpublished states are absent.

Do not replace database-backed authorization tests with UI visibility tests. Hiding navigation is not authorization. Do not weaken environment validators or service transition rules to simplify fixtures.

## Before production

Add hosted Supabase JWT/JWKS/callback tests, R2 bucket-policy and signed-URL tests, the selected production malware-scanner adapter/integration tests, multi-replica/edge abuse-control tests, browser accessibility automation plus manual WCAG review, continuous dependency/secret scanning, backup/restore exercises, and deployment health/rollback tests.
