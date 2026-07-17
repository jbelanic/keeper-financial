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

## Phase 1F candidate-entry readiness additions

- Run callback tests against the genuine local Supabase Auth service: create a unique account from a published synthetic posting, consume the Mailpit confirmation link, exchange the real callback code, and prove exactly-once posting-bound application start.
- Add password sign-in tests for both modes: posting-bound existing-user sign-in must preserve the safe posting slug and invoke narrow provisioning; generic sign-in must remain non-provisioning and deny an unmapped identity.
- Verify API authorization with genuine locally issued Supabase ES256 JWTs and the live local JWKS endpoint, including issuer, audience, signature, verified-email, AAL1/AAL2, expiry, key mismatch, and unmapped-subject cases. Development identity headers are not acceptable evidence for this gate.
- Exercise Supabase SSR cookies through callback, server component, browser request, refresh-token rotation, cross-request persistence, expiry, revocation, and sign-in redirection. Assert that tokens and cookie values never enter logs, URLs, rendered output, or audit metadata.
- Add browser E2E coverage from the published posting through registration and through existing-user sign-in to the posting-specific application. Include confirmation via Mailpit, retry/idempotency, closed/unknown posting failure, unmapped-user recovery, refresh, and return after a new browser request.
- Add navigation tests proving eligible candidates can discover candidate onboarding and authorized admins can discover onboarding administration, while direct routes retain server-side authorization and ineligible users receive no unauthorized data.
- Replace candidate-wide lifecycle characterization with application-specific transition tests: multiple applications for one candidate, valid transition maps per application, cross-application isolation, required reasons, status history, and audit evidence.
- Add onboarding assignment tests that require the intended application to be `conditionally_selected`, reject selection that belongs only to another application, reject inactive/unknown plans, and preserve an existing valid assignment on failure.
- Add acknowledgement authorization tests that permit only the exact issued document version assigned through the candidate's active onboarding assignment and reject arbitrary, unassigned, superseded-only, and cross-candidate versions.
- Keep activation tests bounded to allow-listed gate satisfaction and `activation_ready`. Assert that readiness does not create an active agent relationship or perform final activation.

## Phase 1D additions

- Review tests cover admin authorization, queue filtering, suspended/terminal exclusion, interview recording, information requests, allowed/invalid decisions, required decline reasons, status history, and audit evidence.
- Onboarding tests cover bounded plan/task creation, eligible assignment, candidate-owned dashboard/evidence, administrative review, exact-version acknowledgement, external envelope references, allow-listed gates, and activation-readiness calculation. The Phase 1F readiness additions above are required to close the discovered application-specific lifecycle, active-plan, assignment-bound acknowledgement, and navigation defects.
- Phase 1D contract tests pin review/onboarding route security and response shapes; web tests cover the admin review pipeline, onboarding administration, and candidate task dashboard.

## Phase 1E additions

- Agent tests cover full admin denial/MFA and active-relationship matrices, bounded create/list/get/update, row locking, duplicate conflicts, approval transitions, published-edit reset, suspension reason, public filtering, safe projections, and configured attribution.
- Migration tests verify the agent-profile schema at `20260717_0005`; contract tests pin public versus protected agent operations.
- Web tests cover public directory/detail states and admin profile create/edit/lifecycle behavior.

## ClamAV and upload validation

- Scanner unit tests cover framed `INSTREAM`, bounded chunks/responses, clean and detection results, connection/timeouts/protocol failures, and fail-closed configuration.
- Upload tests cover AAL2, exact size limits, declared/detected type and structure agreement, malformed and decompression-bomb inputs, safe errors, scan-only non-persistence, clean-before-MinIO ordering, and database/storage cleanup.
- The in-memory verifier checks both a clean sample and the standard antivirus test marker without writing sample bytes to disk.

## Migrations and generated contracts

- Run `alembic upgrade head`, `alembic current --check-heads`, and `alembic check` against PostgreSQL. Reaching head and autogeneration drift are separate results; the known Phase 1D model/schema drift remains a Phase 1F blocker.
- Run `make openapi` twice and compare output hashes. OpenAPI, generated TypeScript declarations, runtime routes, schemas, and frontend types must change together.
- Never rewrite an issued migration to silence drift; add a reviewed forward migration when remediation is approved.

## Security regression validation

- Preserve the complete anonymous, unmapped, wrong-role, inactive/lifecycle-denied, missing-AAL2, authorized, and cross-owner matrices for protected resources.
- Exercise safe `404` behavior, no-store responses, structured audit minimization, log redaction, immutable submitted content, private-object policy, and fail-closed environment guards.
- Keep dependency, secret, static-analysis, and container-image checks in the release evidence; no scanner finding may be hidden by weakening runtime controls.

## Local-stack validation

- Render the tracked Compose configuration from `.env.example` without reading a real `.env`.
- Verify PostgreSQL, MinIO, bucket initialization, ClamAV, API, frontend, Supabase Auth/JWKS, local mail capture, and local-only Studio operation on Linux Mint.
- Probe `/health`, `/health/db`, MinIO live health, ClamAV clean/detection behavior, application routes, loopback bindings, service logs, and migration head.
- Confirm Supabase Storage and its S3 protocol remain disabled; application objects must continue to use private MinIO.

Production readiness still requires browser-based automated accessibility and visual-regression coverage at agreed viewports plus manual keyboard, zoom, screen-reader, contrast, and 320 CSS-pixel review.

## Security regression expectations

Every protected route must add tests for anonymous, authenticated-but-unmapped, wrong-role, inactive/lifecycle-denied, and authorized access. Every candidate-owned resource must include cross-candidate identifier tests. New status operations must include invalid transitions and required-reason tests. New public data queries must prove unpublished states are absent.

Do not replace database-backed authorization tests with UI visibility tests. Hiding navigation is not authorization. Do not weaken environment validators or service transition rules to simplify fixtures.

## Before production

Complete the Phase 1F candidate-entry readiness tests above; add MinIO bucket-policy and signed-URL tests, expanded adversarial document-corpus tests, deployment-level abuse-control tests, browser accessibility automation plus manual WCAG review, continuous dependency/secret scanning, backup/restore exercises, and Linux Mint deployment health/rollback tests.
