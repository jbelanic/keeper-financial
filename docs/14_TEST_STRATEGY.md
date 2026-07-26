# Test Strategy

## Borrower application additions

- Phase B schema/model/migration tests prove typed versioned payloads, one primary plus at most one co-borrower, constraints/indexes, forward upgrade to one `20260724_0011` head, clean `alembic check`, and generated OpenAPI/TypeScript determinism.
- Phase B capability tests cover entropy, keyed-digest storage, secure-cookie attributes, exact application/origin/CSRF/revision/lifecycle binding, inactivity expiry, replay, wrong/cross-application secrets, indistinguishable denial, no-op activity semantics, and no token leakage.
- Phase B encryption tests use synthetic test keys only and cover AES-GCM round trip, unique nonces, authenticated metadata/purpose binding, wrong/tampered key/nonce/ciphertext/AAD failure, active/old key IDs, malformed key material, serializer/error redaction, and no plaintext persistence.
- Phase B SIN and authorization tests cover nine-digit/Luhn validation, no saved-value return to borrowers, masked projection, explicit AAL2 reveal, safe audit metadata, administrator/exact-assigned-agent matrices, and cross-assignment denial.
- Phase B sequencing tests prove no public submit route exists and no draft internal projection succeeds without durable snapshot/consent evidence. Unit-tested lifecycle primitives do not substitute for the Phase D coordinator.
- Phase D must add document and atomic/idempotent final-submission failure/race/orphan tests; Phase F must add retention/legal-hold/purge/restore tests; Phases C–F must add genuine browser and operational evidence.
- Phase E tests cover the administrator/AAL2 borrower review queue, exact assigned-agent versus wrong-agent access, administrator detail access, active-agent assignment validation and idempotency, masked internal projection, document metadata omission of object keys, API-proxied decrypting document download and safe headers, missing/tampered object denial, bounded SIN reveal reasons, assigned-agent reveal, and safe reveal/audit payloads. Frontend tests cover the minimal admin review console load/assign/reveal/download workflow with mocked bearer transport. PostgreSQL row-lock concurrency remains best evidenced in an isolated database run because SQLite cannot prove lock behavior.
- Genuine integration evidence uses only synthetic borrowers and generated safe documents. Passing source tests alone is not production, privacy, legal, operational, or release acceptance.

## 2026-07-20 onboarding-completion additions

- Unit-test exact Documenso template lookup/use requests, configured signer-role selection, deterministic assignment external ID, echoed source/template/external-ID/recipient/envelope provenance, bounded response parsing, token-derived signing links, and strict same-public-origin signing URLs. Redirect, timeout, oversize, malformed, mismatched provenance, ambiguous recipient, unsupported status, missing link data, and provider failures must remain safe and fail closed.
- API/service tests cover unconditional completion AAL2, authoritative assignment/user recipient projection, withdrawn/stale lifecycle rejection before issuance or activation, manual/recovery-envelope ineligibility, duplicate issuance without provider calls, persistence only after provider success, readiness/provider completion requirements, idempotent role/history/audit transitions, rollback, and eligible-agent projection.
- The opt-in isolated PostgreSQL suite covers completion serialization using real row locks; SQLite unit tests do not substitute for this concurrency evidence.
- Web tests cover send/refresh/recovery states, explicit completion confirmation, completed read-only history, current-envelope-only signing links, safe external-link attributes, and agent-profile continuation.

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
- Web tests cover published/error/empty recruitment rendering, Supabase registration and safe callback provisioning bridge, a nonobstructing section outline, explicit required/optional labels, linked/focused errors, in-place polite save feedback, save-before-review, disclosure visibility, duplicate guards, withdrawal focus restoration, automatic AAL2 document list/empty/retry states, distinct upload errors/list refresh, and admin lifecycle UI.
- OpenAPI tests pin Phase 1C security declarations, route inventory, internal-field exclusions, and server-owned draft exclusions. Generation is run twice and hashes must remain stable.

## Candidate-entry completion additions

The 2026-07-17 candidate-completion remediation implements the source-level
and opt-in integration coverage below. The live-stack cases use
`KEEPER_RUN_LOCAL_AUTH_E2E=1` and synthetic local identities only; absence of
that explicit flag skips rather than mocks the external-state journey.

- Run callback tests against the genuine local Supabase Auth service: create a unique account from a published synthetic posting, consume the Mailpit confirmation link, exchange the real callback code, and prove exactly-once posting-bound application start.
- Add password sign-in tests for both modes: posting-bound existing-user sign-in must preserve the safe posting slug and invoke narrow provisioning; generic sign-in must remain non-provisioning and deny an unmapped identity.
- Verify API authorization with genuine locally issued Supabase ES256 JWTs, the live local JWKS endpoint, and bearer-authenticated local Auth `/user` confirmation, including issuer, audience, signature, authoritative confirmed email, AAL1/AAL2, expiry, key mismatch, invalid/unmapped subject, and provider-unavailability cases. User-editable metadata is not confirmation evidence, and development identity headers are not acceptable evidence for this gate.
- Exercise Supabase SSR cookies through callback, server component, browser request, refresh-token rotation, cross-request persistence, expiry, revocation, and sign-in redirection. Assert that tokens and cookie values never enter logs, URLs, rendered output, or audit metadata.
- Add browser E2E coverage from the published posting through registration and through existing-user sign-in to the posting-specific application. Include confirmation via Mailpit, retry/idempotency, closed/unknown posting failure, unmapped-user recovery, refresh, and return after a new browser request.
- Add navigation tests proving eligible candidates can discover candidate onboarding and authorized admins can discover onboarding administration, while direct routes retain server-side authorization and ineligible users receive no unauthorized data.
- Replace candidate-wide lifecycle characterization with application-specific transition tests: multiple applications for one candidate, valid transition maps per application, cross-application isolation, required reasons, status history, and audit evidence.
- Add onboarding assignment tests that require the intended application to be `conditionally_selected`, reject selection that belongs only to another application, reject inactive/unknown plans, and preserve an existing valid assignment on failure.
- Add acknowledgement authorization tests that permit only the exact issued document version assigned through the candidate's active onboarding assignment and reject arbitrary, unassigned, superseded-only, and cross-candidate versions.
- Keep activation tests bounded to allow-listed gate satisfaction and `activation_ready`. Assert that readiness does not create an active agent relationship or perform final activation.

The 2026-07-18 live synthetic run passed both enabled candidate-auth cases: Mailpit confirmation exchanged the PKCE callback and entered the posting-specific application with a persistent cookie session; a separately confirmed unmapped identity remained denied after generic sign-in and provisioned only after posting-bound existing-user sign-in. The ordinary isolated suite still skips these live cases unless explicitly enabled.

### Local administrator bootstrap and AAL2 additions

- Run the linker's database-backed unit tests for placeholder replacement, same-subject idempotency, inactive/wrong-role/missing-identity rejection, genuine-subject protection, duplicate-subject rejection, invalid email/UUID, explicit non-local refusal, and transaction rollback.
- Keep command tests free of the current application database. Unit sessions use synthetic isolated databases; no test creates a Supabase Auth user or exercises service-role credentials.
- Exercise the browser TOTP states for a verified factor challenge, new factor enrollment, already-AAL2 session, and bounded provider failure. Assert that the workflow does not expose raw provider errors.
- Run the admin authorization matrix with MFA enforcement enabled: linked admin AAL1 fails the access probe and protected admin route, linked admin AAL2 succeeds, and candidate/unmapped AAL2 identities remain denied. An admin `returnTo` value must remain non-provisioning and incapable of elevation.
- The genuine local operator procedure creates and auto-verifies a synthetic Auth user in loopback-only Studio, links only its UUID through the approved command, completes browser TOTP, and proves admin access. The 2026-07-18 implementation report records the successful live ceremony separately from deterministic tests; future release-host validation must repeat it with disposable local data.

## Phase 1D additions

- Review tests cover admin authorization, queue filtering, suspended/terminal exclusion, interview recording, information requests, allowed/invalid decisions, required decline reasons, status history, and audit evidence.
- Onboarding tests cover bounded plan/task creation, eligible assignment, candidate-owned dashboard/evidence, administrative review, exact-version acknowledgement, external envelope references, allow-listed gates, and activation-readiness calculation. The candidate-entry completion coverage above closes the discovered application-specific lifecycle, active-plan, assignment-bound acknowledgement, and navigation source defects.
- Phase 1D contract tests pin review/onboarding route security and response shapes; web tests cover the admin review pipeline, onboarding administration, and candidate task dashboard.

## Phase 1E additions

- Agent tests cover full admin denial/MFA and active-relationship matrices, bounded create/list/get/update, row locking, duplicate conflicts, approval transitions, published-edit reset, suspension reason, public filtering, safe projections, and configured attribution.
- Migration tests verify the agent-profile schema at `20260717_0005`; contract tests pin public versus protected agent operations.
- Web tests cover public directory/detail states and admin profile create/edit/lifecycle behavior.

## 2026-07-19 operator-workflow refinement additions

- Plan tests cover initial task authoring/order, unused-plan content and availability edits, first-assignment lock enforcement, permanent referenced-plan immutability, inactive-plan recovery, and explicit lock projection to the administrator UI.
- Assignment tests cover readable exact-application selection, assignment isolation across repeat attempts/generations, exact-assignment readiness projection, read-only superseded history, and rejection of cross-assignment gate, policy, task, and e-sign evidence. An opt-in isolated PostgreSQL race test proves simultaneous assignments across different applications and plans leave exactly one active assignment for the candidate.
- Gate tests distinguish the three manual codes from the two derived-only codes, require bounded evidence for satisfaction, require a reason for correction/reopen, and preserve append-only evidence events. An opt-in isolated PostgreSQL race test proves simultaneous manual satisfaction commits exactly one transition/evidence event.
- Documenso adapter tests cover configured HTTPS origin, quoted document identifiers, redirect refusal, malformed JSON, provider/network failures, attempted origin escape, and recognized versus fail-closed status mapping. Envelope tests cover provider-authoritative refresh, provider/DRAFT failure reopening, and replacement without predecessor deletion. An opt-in isolated PostgreSQL race test proves a delayed completed refresh cannot mutate or satisfy a concurrently replaced predecessor.
- Agent-profile tests cover server-projected eligibility, readable selection, slug validation/availability, first-publication lock, permanent reservation after unpublishing, and server-side rejection of locked-slug changes.
- Web tests cover unused-plan task editing/ordering and lock state, exact-application assignment without raw-ID entry, manual versus derived gate controls, provider refresh/replacement controls, eligible-agent selection, slug feedback, and first-publication slug disabling.
- Migration verification must exercise blank upgrade to `20260719_0008`, one-head assertion, `alembic check`, downgrade to `20260718_0007`, and re-upgrade in an isolated PostgreSQL database. Populated tests must prove audit-derived historical slug locking and pre-DDL refusal of duplicate legacy provider envelope IDs on upgrade or rejected-envelope evidence on downgrade. Legacy rows whose exact assignment cannot be proved must remain non-satisfying.

## ClamAV and upload validation

- Scanner unit tests cover framed `INSTREAM`, bounded chunks/responses, clean and detection results, connection/timeouts/protocol failures, and fail-closed configuration.
- Upload tests cover AAL2/ownership, exact size limits, declared/detected type
  and structure agreement, common readable PDFs, standard Office-generated and
  streaming-data-descriptor DOCX, official/ZIP libmagic results, narrow valid
  legacy DOC, malformed/truncated/polyglot input, missing DOCX parts, traversal,
  encryption, macros, expansion/ratio limits, arbitrary ZIP/OLE rejection, safe
  error categories, scan-only non-persistence, clean-before-MinIO ordering, and
  database/storage cleanup.
- The in-memory verifier checks both a clean sample and the standard antivirus test marker without writing sample bytes to disk.
- The opt-in local journey may receive operator-controlled synthetic PDF/DOCX
  paths through process-only test variables. It performs real browser file
  selection, TOTP/AAL2, ClamAV/MinIO upload, metadata refresh, invalid-structure
  rejection, unauthenticated download denial, and factor cleanup without
  printing credentials, setup secrets, file names, or object keys.

## Migrations and generated contracts

- Run `alembic upgrade head`, `alembic current --check-heads`, and `alembic check` against PostgreSQL. Reaching head and autogeneration drift are separate results.
- Run `make openapi` twice and compare output hashes. OpenAPI, generated TypeScript declarations, runtime routes, schemas, and frontend types must change together.
- Never rewrite an issued migration to silence drift; add a reviewed forward migration when remediation is approved.
- Candidate remediation migration `20260717_0006` and schema-drift migration
  `20260718_0007` have separate focused coverage; the latter pins issued-file
  hashes, the single head, authoritative model metadata, exact PostgreSQL index
  columns/order, and exact FK delete actions.
- Run the Step 9 PostgreSQL tests with
  `KEEPER_RUN_SCHEMA_MIGRATION_E2E=1`. They use randomly named temporary local
  databases to prove `0006 → 0007 → 0006 → 0007`, direct fresh upgrade to head,
  representative evidence survival, deletion restrictions, nullable unreviewed
  tasks, catalog/metadata agreement, and clean `alembic check`.

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

Preserve the completed candidate-entry tests above; add MinIO bucket-policy and signed-URL tests, expanded adversarial document-corpus tests, deployment-level abuse-control tests, browser accessibility automation plus manual accessibility review, continuous dependency/secret scanning, backup/restore exercises, alert testing, and Linux Mint deployment health/rollback tests.

An owner-operated administrator information-request browser ceremony and a genuine second-candidate cross-account denial may be retained as additional release assurance. Their absence is not an uncommitted source-completion blocker because deterministic authorization and realistic integration coverage are already part of the merged evidence. Neither ceremony alone is production approval.

## 2026-07-18 browser-completion additions

- Candidate-shell tests prove the shared layout calls only the minimal availability endpoint once, hides onboarding before assignment, shows it after an application-bound assignment, maps no assignment to a stable dashboard, and offers only a manual retry for transient dashboard failure.
- Form tests pin visible Phase 1C limits, canonical month controls, referral-detail clearing, client preflight, safe API `422` path mapping, linked error summaries, value preservation, valid draft/revision behavior, immutable submission, and stale-revision denial.
- Candidate MFA tests cover no factor, verified factor at AAL1, already AAL2, incomplete-factor cleanup, bounded provider/challenge failures, session refresh plus post-refresh AAL2 proof, exact document return, invalid-return fallback, cross-owner denial, and no admin elevation.
- Admin tests select one exact posting/attempt, require its `application_id`, enforce the information-request lifecycle matrix, reject candidate/application mismatch, preserve other attempts, and pin operation-specific conflict text plus application history/audit evidence.
- The opt-in genuine Firefox case closes and recreates the candidate tab three
  times, performs ordinary posting-bound sign-in without focus/visibility/
  resize assistance, requires a terminal application or bounded error state,
  saves near the bottom with stable scroll and focus, and then exercises real
  candidate TOTP/AAL2 plus clean ClamAV/MinIO upload and metadata refresh.
- Responsive browser evidence measures overflow and shared container geometry
  at 320, 375, 768, 1024, 1280, 1366, 1536, and 1920 CSS pixels at normal zoom.

## Phase C borrower-web additions

- API-client tests pin same-origin relative paths, `credentials: include`, `cache: no-store`, CSRF headers, optimistic revisions, bounded validation errors, and opaque-ID-only recovery.
- Component tests cover start/recovery, successful section advancement, failure value/step preservation, focused accessible error summary, masked/provided SIN replacement, one co-borrower, stable repeat controls, synthetic versioned consent, and the absence of a submit request.
- Source regression tests reject application-answer/SIN persistence, console/analytics calls, and borrower submission paths. Proxy tests prove exact application-host routing, conflicting forwarded-host refusal, borrower-only API proxying, and no Supabase call in the accountless flow.
- The production build proves `/mortgage-application` is dynamic and not statically embedded with borrower answers. No Chromium/Playwright executable is installed in the Phase C worktree, and sandbox port binding is denied, so genuine-browser keyboard, zoom, network inspection, and measured 320 CSS-pixel reflow remain explicit acceptance evidence rather than being inferred from jsdom/CSS tests.
