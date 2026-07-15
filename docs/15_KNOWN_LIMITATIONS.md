# Known Limitations

Phase 1C is a reviewable local engineering implementation on top of Phases 0–1B. It is not a production launch, legal/compliance approval, formal accessibility certification, or authorization to process real candidate data.

## Recruitment and privacy boundary

- `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md` resolves the questionnaire, cardinality/reapplication, post-withdrawal access, document categories, candidate disclosure/version, and candidate MFA policy. The implementation does not broaden those allow-lists.
- Candidate review queues/details, internal-note authoring, information requests/reopening, interview/selection/decline operations, onboarding, controlled-document issuance, acknowledgements/e-signature, activation, and agent-profile expansion remain Phase 1D/1E work. The premature candidate transition API is unmounted; existing foundation models/services are not an operational Phase 1D workflow.
- Candidate-visible messages are intentionally empty until a later controlled authoring workflow exists. Candidate contracts omit internal reasons, notes, actors, decisions, and audit metadata.
- No real recruitment posting is supplied. Local seed postings are conspicuously `SYNTHETIC`, `example.test`-only, and gated to `APP_ENV=local`.
- Legal retention periods remain unresolved. The disclosure truthfully describes policy-controlled categories without a fabricated period; deletion/de-identification jobs, legal/security holds, and production retention operations are not implemented.
- Email notification behavior/provider is unresolved and no recruitment email is sent. Candidate registration/verification email is delegated to configured Supabase Auth.

## File, identity, and production integrations

- `local_test` is a deterministic local/test scanner adapter, not malware protection. No production malware-scanning provider is selected. Nonlocal configuration prohibits that adapter and upload fails closed when scanning is disabled/unavailable.
- The private R2 adapter exists, but hosted R2 credentials, bucket-policy probes, signed-URL behavior, orphan reconciliation operations, and a production scanner integration require controlled non-production validation. No credentials or private objects are committed.
- Hosted Supabase issuer/JWKS, email delivery, callback/account recovery, revocation/offboarding, and real AAL2 ceremonies require controlled integration testing. Supabase identity alone still receives no local application access.
- Application start serializes on the published posting and PostgreSQL tests prove concurrent start/submission exactly once. Production-scale contention/load, multi-region behavior, and disaster recovery remain untested.

## Preserved product/operations limitations

- Phase 1B lead notification/assignment/CRM/export/customer-withdrawal and distributed abuse controls remain deferred. Mortgage redirect is configuration-only; CRM/e-signature provider labels remain disabled.
- Mortgage origination, borrower identity/financial/document data, underwriting, lender submission, commissions/payroll, custom signing, automated FSRA verification, and independent agent portals remain explicitly out of scope.
- Production monitoring/error reporting, backups and restore drills, incident response, access review, vendor/subprocessor registers, privacy/security operations, deployment hosting, and release approval remain unresolved.
- Audit events are append-oriented through application APIs, but dedicated database privileges, retention, immutable export/tamper evidence, and operational review remain production work.
- UI tests cover semantic controls, text status, focus/error/live-region behavior, duplicate actions, and responsive CSS guardrails. Manual keyboard, zoom, screen-reader, contrast, reduced-motion, touch-target, and 320 CSS-pixel cross-browser review is still required; no WCAG certification is claimed.
- Owner approval/licensing remains required for the Phase 1A logo/font/photography and final public legal/regulatory presentation.

Exact local validation, scanner findings, and any unavailable external checks are recorded in `docs/20_PHASE_1C_IMPLEMENTATION_REPORT.md`.
