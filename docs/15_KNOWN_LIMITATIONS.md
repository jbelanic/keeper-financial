# Known Limitations

The current approved checkpoint is Phase 1D at `6349c16`, Phase 1E at `384246c`, and fail-closed local ClamAV at `e9d9f65`, operating through Docker on the Linux Mint host. This checkpoint does not itself provide legal/compliance approval, formal accessibility certification, security hardening, or authorization to process real candidate or borrower data. Phase 1F readiness planning and blocker resolution is next.

## Recruitment and privacy boundary

- `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md` resolves the questionnaire, cardinality/reapplication, post-withdrawal access, document categories, candidate disclosure/version, and candidate MFA policy. The implementation does not broaden those allow-lists.
- **Candidate entry and recovery:** the remediation worktree exposes both registration and existing-user sign-in from a published posting. Both use a server-validated slug and converge on the narrow application-start boundary. Generic sign-in remains non-provisioning, and an unmapped identity without posting context remains denied.
- **Session evidence:** source-level tests cover callback exchange, response-cookie persistence, protected-request refresh propagation, and expired/invalid-session denial. The opt-in full local Supabase/Mailpit registration and posting-bound recovery journey passed with fresh synthetic identities on 2026-07-18. The separate genuine-token JWT/JWKS case remains opt-in, and the successful journey is not proof of refresh-token revocation/offboarding behavior.
- Phase 1D implements the authorized review queue/detail, interview status, information requests, decisions, reusable onboarding plans, candidate task evidence/review, controlled-document projections, exact-version acknowledgement, external envelope tracking, and allow-listed activation gates. Submitted candidate questionnaires remain immutable.
- **Navigation:** the candidate shell discovers onboarding only when the protected dashboard proves an eligible current assignment; the authorized admin shell exposes onboarding administration. Direct-route/API authorization remains authoritative.
- **Lifecycle and assignment:** review and decision mutations now lock and transition the exact `CandidateApplication` attempt. Assignment requires that exact attempt to be `conditionally_selected` and its plan to be active, then records application/assignment/task provenance without overwriting prior application history.
- **Controlled-document acknowledgement:** each assignment snapshots exact eligible versions. Acknowledgement requires the candidate actor, current assignment, and exact assignment/version relationship; unassigned, cross-candidate, superseded/ineligible, and arbitrary versions fail closed.
- Activation-gate satisfaction and `activation_ready` calculation are implemented. There is no separately approved final activation operation; readiness must not be described as an activated agent relationship.
- Agent-profile administration, approval, published directory/detail projections, suspension/archive removal, and safe configured attribution are implemented in Phase 1E. Agent-proposed updates remain P1, and the independent microsite builder remains deferred/P2. Admin profile creation currently identifies an already authorized active local agent relationship by UUID; it does not provision or reactivate agent accounts.
- Candidate-visible messages are intentionally empty until a later controlled authoring workflow exists. Candidate contracts omit internal reasons, notes, actors, decisions, and audit metadata.
- No real recruitment posting is supplied. Local seed postings are conspicuously `SYNTHETIC`, `example.test`-only, and gated to `APP_ENV=local`.
- Legal retention periods remain unresolved. The disclosure truthfully describes policy-controlled categories without a fabricated period; deletion/de-identification jobs, legal/security holds, and production retention operations are not implemented.
- Email notification behavior/provider is unresolved and no recruitment email is sent. Candidate registration/verification email is delegated to configured Supabase Auth.

## File, identity, and production integrations

- Local ClamAV is implemented and required by the live stack. `local_test` remains deterministic test plumbing and production rejects it. ClamAV detection depends on current signatures and engine quality; a clean result reduces risk but is not proof of semantic safety. FreshClam update failures require operational monitoring.
- Clamd TCP has no application authentication or transport encryption. It is restricted to the Compose network and host loopback, but any process already able to connect locally can submit scan traffic. Port 3310 must never be bound to a public interface.
- PDF/JPEG/PNG scan-only uploads receive libmagic plus structural validation.
  Phase 1C résumé/cover-letter PDF/DOC/DOCX now accept realistic common PDF
  comment tails and standard DOCX ZIP data descriptors while retaining bounded
  PDF readability, narrow Word OLE, strict OPC/WordprocessingML, expansion,
  traversal, encryption, macro, ClamAV, and private-storage controls. Complex
  Office formats still retain greater parser risk than PDF or safe raster
  images.
- MinIO is wired through the implemented private S3 adapter with path-style addressing and a private initialized bucket. Docker access is verified: the immutable MinIO server is healthy and `minio-init` completed successfully. Genuine synthetic candidate AAL2 uploads of standard office-generated PDF and DOCX passed through browser controls and the API, real ClamAV, MinIO persistence, and metadata refresh, with unauthenticated download denied. Authorized signed-download behavior, backup/restore, bucket-policy probes, and orphan reconciliation remain unverified.
- Current auth/session code genuinely requires Supabase semantics, so the live stack uses the repository-tracked local Supabase CLI configuration. `npx supabase` 2.109.1 is available; no global binary is installed. The config enables email confirmation/local Mailpit capture and TOTP MFA while disabling independently optional services. Mailpit capture is not real mail delivery. The worktree provides a placeholder-only, local-operator admin identity link command plus browser TOTP enrollment/verification; it never links by email automatically or grants a role. The candidate integration journey and genuine admin link/TOTP/AAL2 ceremony now have local synthetic evidence, including authorized `/admin`, `/admin/candidates`, and `/admin/onboarding` navigation. Revocation/offboarding remain operational validation work. The upstream local stack is not production-hardened; its CLI-managed ports bind broadly, require host-firewall protection, and must not be externally reachable. Supabase identity alone still grants no ordinary local portal access; the validated posting-bound start is the explicit narrow operation permitted to create candidate access.
- Supabase Studio may be enabled only for local operator use and must not be exposed to an untrusted network. Supabase Storage and its S3 protocol remain disabled; they are not an alternative application object store.
- The candidate remediation introduced `20260717_0006`. The uncommitted Step 9
  worktree adds forward revision `20260718_0007` for the separate Phase 1D
  index/foreign-key drift without rewriting issued history. Isolated
  PostgreSQL upgrade/downgrade/re-upgrade and fresh-head tests preserve
  synthetic evidence and verify exact catalog definitions; owner review and
  commit remain required before this becomes an approved checkpoint.
- The rebuilt/recreated web and API containers are healthy, and live inspection verifies that web, API, PostgreSQL, and MinIO are loopback-bound. Web `/` and `/agents` return success; API `/health/db` reports the database reachable. This does not change the separate broad Supabase CLI port-binding caveat above.
- Application start serializes on the published posting and PostgreSQL tests prove concurrent start/submission exactly once. Production-scale contention/load, multi-region behavior, and disaster recovery remain untested.

## Phase 1F readiness limitations

- Phase 1B lead notification/assignment/CRM/export/customer-withdrawal and distributed abuse controls remain deferred. Mortgage redirect and agent-specific destinations are configuration-only and fail closed; no agent mapping is supplied by default. CRM/e-signature provider labels remain disabled.
- Mortgage origination, borrower identity/financial/document data, underwriting, lender submission, commissions/payroll, custom signing, automated FSRA verification, and independent agent portals remain explicitly out of scope.
- Production monitoring/error reporting, PostgreSQL/MinIO/Supabase backup and restore drills, incident response, access review, privacy/security operations, host hardening, and release approval remain unresolved. The deployment host itself is no longer an open selection.
- The uncommitted Step 9 forward migration resolves the known general Phase 1D
  index/foreign-key metadata drift locally. It is not launch approval: owner
  review and commit of `20260718_0007` remain required, along with the other
  Phase 1F readiness gates.
- Legacy review/onboarding rows whose correct application or assignment cannot be proved remain nullable and are rejected by new mutation/readiness paths. No guess-based backfill is performed; an owner-approved data reconciliation would be required if such rows exist in a retained environment.
- Linux Mint reconstruction proves local operability, not disaster recovery or portability to an untested host. A repeatable rebuild/restore drill and recorded rollback remain Phase 1F work.
- Audit events are append-oriented through application APIs, but dedicated database privileges, retention, immutable export/tamper evidence, and operational review remain production work.
- UI tests cover semantic controls, text status, focus/error/live-region behavior, duplicate actions, and responsive CSS guardrails. Genuine Firefox now covers the required 320–1920 CSS-pixel reflow set at normal zoom and three closed-tab candidate sign-ins; manual keyboard, screen-reader, contrast, reduced-motion, touch-target, zoom variation, and cross-browser review are still required. No WCAG certification is claimed.
- Owner approval/licensing remains required for the Phase 1A logo/font/photography and final public legal/regulatory presentation.

Current local-Docker operation and validation evidence is recorded in `docs/LOCAL_DEVELOPMENT.md`; historical phase evidence remains in the phase implementation reports.

The browser-completion implementation has deterministic coverage for
no-assignment stability, field guidance/`422` mapping, candidate TOTP step-up,
and application-specific information requests. The fresh genuine candidate
journey passed, including real TOTP AAL2 and owned document metadata access. A
fresh genuine admin-browser information request remains required before this
worktree may be described as ready to commit; source-level success alone is not
release evidence.
