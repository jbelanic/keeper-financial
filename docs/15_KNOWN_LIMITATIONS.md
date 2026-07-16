# Known Limitations

Phase 1E targets the owner-approved live/production environment: Docker on the local Linux host. That deployment decision does not itself provide legal/compliance approval, formal accessibility certification, security hardening, or authorization to process real candidate or borrower data.

## Recruitment and privacy boundary

- `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md` resolves the questionnaire, cardinality/reapplication, post-withdrawal access, document categories, candidate disclosure/version, and candidate MFA policy. The implementation does not broaden those allow-lists.
- Agent-profile administration, approval, published directory/detail projections, suspension/archive removal, and safe configured attribution are implemented in Phase 1E. Agent-proposed updates remain P1, and the independent microsite builder remains deferred/P2. Admin profile creation currently identifies an already authorized active local agent relationship by UUID; it does not provision or reactivate agent accounts.
- Candidate-visible messages are intentionally empty until a later controlled authoring workflow exists. Candidate contracts omit internal reasons, notes, actors, decisions, and audit metadata.
- No real recruitment posting is supplied. Local seed postings are conspicuously `SYNTHETIC`, `example.test`-only, and gated to `APP_ENV=local`.
- Legal retention periods remain unresolved. The disclosure truthfully describes policy-controlled categories without a fabricated period; deletion/de-identification jobs, legal/security holds, and production retention operations are not implemented.
- Email notification behavior/provider is unresolved and no recruitment email is sent. Candidate registration/verification email is delegated to configured Supabase Auth.

## File, identity, and production integrations

- `local_test` is a deterministic test adapter, not malware protection. The live stack sets scanning to `disabled`, so candidate upload fails closed until an approved local scanner is implemented.
- MinIO is wired through the implemented private S3 adapter with path-style addressing and a private initialized bucket. Docker access is verified: the immutable MinIO server is healthy and `minio-init` completed successfully. End-to-end object I/O, signed-download behavior, backup/restore, bucket-policy probes, and orphan reconciliation remain unverified.
- Current auth/session code genuinely requires Supabase semantics, so the live stack uses the repository-tracked local Supabase CLI configuration. `npx supabase` 2.109.1 is available; no global binary is installed. After the old `keeper-financial-local` stack was stopped without discarding its backup, the tracked `project_id = "keeper-financial"` configuration started successfully with an ignored mode-`0600` ES256 signing-key file. Local Auth health succeeds, and JWKS returns HTTP `200` with exactly one ES256 key. The config enables email confirmation/local mail capture and TOTP MFA while disabling independently optional services, but local SMTP capture is not real mail delivery; callback/account-recovery, revocation/offboarding, and real AAL2 ceremonies remain unverified. The upstream local stack is not production-hardened; its CLI-managed ports bind broadly, require host-firewall protection, and must not be externally reachable. Supabase identity alone still grants no local application access.
- Live migration reachability is verified at `20260717_0005`, and API/database health returned `200`. `alembic check` remains non-green because of pre-existing Phase 1D index and foreign-key `ondelete` model/schema drift; it is a known diagnostic limitation, not a bootstrap blocker or evidence that this deployment change should rewrite historical migrations.
- The rebuilt/recreated web and API containers are healthy, and live inspection verifies that web, API, PostgreSQL, and MinIO are loopback-bound. Web `/` and `/agents` return success; API `/health/db` reports the database reachable. This does not change the separate broad Supabase CLI port-binding caveat above.
- Application start serializes on the published posting and PostgreSQL tests prove concurrent start/submission exactly once. Production-scale contention/load, multi-region behavior, and disaster recovery remain untested.

## Preserved product/operations limitations

- Phase 1B lead notification/assignment/CRM/export/customer-withdrawal and distributed abuse controls remain deferred. Mortgage redirect and agent-specific destinations are configuration-only and fail closed; no agent mapping is supplied by default. CRM/e-signature provider labels remain disabled.
- Mortgage origination, borrower identity/financial/document data, underwriting, lender submission, commissions/payroll, custom signing, automated FSRA verification, and independent agent portals remain explicitly out of scope.
- Production monitoring/error reporting, PostgreSQL/MinIO/Supabase backup and restore drills, incident response, access review, privacy/security operations, host hardening, and release approval remain unresolved. The deployment host itself is no longer an open selection.
- Audit events are append-oriented through application APIs, but dedicated database privileges, retention, immutable export/tamper evidence, and operational review remain production work.
- UI tests cover semantic controls, text status, focus/error/live-region behavior, duplicate actions, and responsive CSS guardrails. Manual keyboard, zoom, screen-reader, contrast, reduced-motion, touch-target, and 320 CSS-pixel cross-browser review is still required; no WCAG certification is claimed.
- Owner approval/licensing remains required for the Phase 1A logo/font/photography and final public legal/regulatory presentation.

Current local-Docker operation and validation evidence is recorded in `docs/LOCAL_DEVELOPMENT.md`; historical phase evidence remains in the phase implementation reports.
