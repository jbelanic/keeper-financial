# Known Limitations

## 2026-07-20 onboarding-completion compatibility ceremony

Source supports the bounded configured-template issuance and explicit atomic completion workflow, but no live Documenso ceremony has been run in this worktree. The adapter now matches the current official v2 template/document reference: before distribution, Keeper verifies that `GET /template/{templateId}` returns the exact configured numeric template `id` and only the configured signer slot; `POST /template/use` must then return a non-empty bounded string document `id`, `DOCUMENT` type, supported distributed status, `TEMPLATE` source, deterministic assignment external ID, and exactly one `SIGNER` recipient with the authoritative email. Keeper accepts an explicit same-origin `/sign/{token}` URL with one non-empty token segment or derives that same path from the provider-returned bounded recipient token. Status refresh requires `GET /envelope/{id}` to echo that exact top-level `id` and an allow-listed status. Any incompatible response fails closed without a local envelope until the owner approves a documented compatibility adaptation. Official reference reviewed on 2026-07-20: <https://openapi.documenso.com/> and <https://docs.documenso.com/docs/developers/api/templates>.

The remaining ceremony is: configure the approved ICA template and signer-recipient IDs; send one synthetic agreement; open the returned signing link; exercise failed/recovery-only safe reissuance; sign the current replacement; refresh provider state to completed; explicitly complete onboarding; verify the user appears in the eligible agent-profile selector. This is not production/pilot approval and does not add webhooks, agreement authoring/storage, automatic profiles/publication, or broad Phase 1F readiness.

The Phase B branch remains based on `origin/main` at `1acf8b6f409284b9dd386cfe6403fd7c266a975d`. Historical checkpoints remain documented in their original reports.

The current baseline includes the explicitly owner-accepted 2026-07-19 operator-workflow refinement and later forward migrations through `20260722_0010`. Historical `20260719_0008` migration evidence remains valid for that checkpoint. Completed Git publication does not authorize deployment, shared-database migration, production/pilot operation, credential/external-service changes, legal/privacy/regulatory/claims/accessibility approval, or processing of real candidate or borrower data.

The Phase B secure borrower foundation is implemented and validated as source on `feat/borrower-secure-foundation`. This is not owner acceptance and is not a deployable borrower intake.

## Borrower application limitations after Phase D.1 source

- Phase C replaces the web entry dependency on the former configuration-only external redirect with an exact-origin Keeper-native borrower form. Phase D.1 adds source-validated borrower object persistence and final submission, but the work remains unaccepted source work and is not deployed.
- Phase B provides borrower models/migration, typed encrypted draft revisions, capability authorization, SIN masking/reveal primitives, exact-assignment internal authorization, and consent/snapshot/legal-hold schema primitives. Phase C provides the web UI and browser draft client. Phase D.1 provides document upload, immutable encrypted snapshot creation, consent binding, and capability revocation. Phase E adds the bounded internal administrator review queue, assignment/reassignment to active agents, exact assigned-agent/admin masked review, document metadata, API-proxied decrypting downloads, and assigned-agent/admin SIN reveal. Purge/legal-hold operations, dedicated TLS ingress, genuine-browser evidence, and operational readiness remain pending.
- The Phase C API integration discrepancy is retained as historical decision evidence in `docs/31_PHASE_C_BORROWER_WEB_FORM_COMPLETION_REPORT.md`. The current source uses the approved deep-merge save path and the web/API subject-property vocabulary is aligned under the recorded option-A decision; broader schema changes remain owner-controlled and are not expanded here.
- Same-browser recovery retains only an opaque application ID in `sessionStorage`; it stores no answers or SIN. The redacted GET returns flags/revision rather than editable answers, so recovery intentionally does not repopulate previously entered ordinary fields.
- Phase E review hardening now rejects assignment targets without an active verified Supabase identity, refuses forward migration when retained borrower documents lack provable encryption payload revision, and bounds encrypted-object downloads. Existing legacy documents require owner-reviewed remediation before migration; no cryptographic provenance is guessed.
- The Phase D.1 submit route exists and coordinates the encrypted snapshot, consent evidence, lifecycle transition, retention date, and capability revocation. The seeded consent catalog wording is a conspicuous placeholder; real-borrower submission must remain disabled until exact owner/legal-approved wording is supplied.
- Borrower settings are typed in API source, but `.env.example` and Compose borrower wiring are not yet present; both borrower feature gates remain off.
- Exact production privacy/credit-use consent wording/version remains unresolved; real-borrower submission must stay disabled.
- Key custody/recovery owners, legal-hold authority, public DNS/TLS ceremony, Caddy configuration, backup/restore/purge drill, monitoring/incident response, and public abuse capacity remain operational blockers.
- No legacy MortgageApp data import is approved. The legacy repository remains unarchived until accepted implementation, deployment, and cutover.

## Recruitment and privacy boundary

- `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md` resolves the questionnaire, cardinality/reapplication, post-withdrawal access, document categories, candidate disclosure/version, and candidate MFA policy. The implementation does not broaden those allow-lists.
- **Candidate entry and recovery:** merged registration and existing-user sign-in start from a published posting. Both use a server-validated slug and converge on the narrow application-start boundary. Generic sign-in remains non-provisioning, and an unmapped identity without posting context remains denied.
- **Session evidence:** source-level tests cover callback exchange, response-cookie persistence, protected-request refresh propagation, and expired/invalid-session denial. The opt-in full local Supabase/Mailpit registration and posting-bound recovery journey passed with fresh synthetic identities on 2026-07-18. The separate genuine-token JWT/JWKS case remains opt-in, and the successful journey is not proof of refresh-token revocation/offboarding behavior.
- Phase 1D plus the operator-workflow refinement implement the authorized review queue/detail, interview status, information requests, decisions, reusable onboarding plans editable only before first assignment, candidate task evidence/review, controlled-document projections, assignment-specific exact-version acknowledgement, Documenso envelope tracking/reconciliation, and bounded manual/derived readiness gates. Submitted candidate questionnaires remain immutable.
- **Navigation:** the candidate shell discovers onboarding only when the protected dashboard proves an eligible current assignment; the authorized admin shell exposes onboarding administration. Direct-route/API authorization remains authoritative.
- **Lifecycle and assignment:** review and decision mutations now lock and transition the exact `CandidateApplication` attempt. Assignment requires that exact attempt to be `conditionally_selected` and its plan to be active, then records application/assignment/task provenance without overwriting prior application history.
- **Controlled-document acknowledgement:** each assignment snapshots exact eligible versions. Acknowledgement requires the candidate actor, current assignment, and exact assignment/version relationship; unassigned, cross-candidate, superseded/ineligible, and arbitrary versions fail closed.
- Activation-gate satisfaction, `activation_ready`, and the separately authorized bounded administrator/AAL2 final completion operation are implemented in this worktree. Manual/recovery agreement links cannot satisfy readiness or completion. This remains source implementation only and is not production/pilot activation authority.
- Agent-profile administration, approval, published directory/detail projections, suspension/archive removal, eligible-agent selection, permanent first-publication slug reservation, and safe configured attribution are implemented in Phase 1E plus the operator-workflow refinement. Agent-proposed updates remain P1, and the independent microsite builder remains deferred/P2. Profile creation does not provision or reactivate agent accounts.
- Candidate-visible messages are limited to bounded open information requests for the exact application. Candidate contracts omit internal interview notes, reasons, actors, decisions, and audit metadata.
- No real recruitment posting is supplied. Local seed postings are conspicuously `SYNTHETIC`, `example.test`-only, and gated to `APP_ENV=local`.
- Candidate legal retention periods remain unresolved. Borrower requirements separately set 30 inactive days for drafts, seven years from original submission for submitted records, active legal-hold exclusion, and rolling 30-day encrypted backups; the jobs and production evidence are not implemented.
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
- Current auth/session code genuinely requires Supabase semantics, so the live stack uses the repository-tracked local Supabase CLI configuration. `npx supabase` 2.109.1 is available; no global binary is installed. The config enables email confirmation/local Mailpit capture and TOTP MFA while disabling independently optional services. Mailpit capture is not real mail delivery. The merged source provides a placeholder-only, local-operator admin identity link command plus browser TOTP enrollment/verification; it never links by email automatically or grants a role. The candidate integration journey and genuine admin link/TOTP/AAL2 ceremony have local synthetic evidence, including authorized `/admin`, `/admin/candidates`, and `/admin/onboarding` navigation. Revocation/offboarding remain operational validation work. The upstream local stack is not production-hardened; its CLI-managed ports bind broadly, require host-firewall protection, and must not be externally reachable. Supabase identity alone still grants no ordinary local portal access; the validated posting-bound start is the explicit narrow operation permitted to create candidate access.
- Supabase Studio may be enabled only for local operator use and must not be exposed to an untrusted network. Supabase Storage and its S3 protocol remain disabled; they are not an alternative application object store.
- Candidate completion introduced `20260717_0006`; merged forward revision
  `20260718_0007` resolves the separate Phase 1D index/foreign-key drift without
  rewriting issued history. The source chain has one head, recorded
  `make migrate-check` evidence is clean, and isolated PostgreSQL
  upgrade/downgrade/re-upgrade and fresh-head tests preserve synthetic evidence
  and verify exact catalog definitions.
- The rebuilt/recreated web and API containers are healthy, and live inspection verifies that web, API, PostgreSQL, and MinIO are loopback-bound. Web `/` and `/agents` return success; API `/health/db` reports the database reachable. This does not change the separate broad Supabase CLI port-binding caveat above.
- Application start serializes on the published posting and PostgreSQL tests prove concurrent start/submission exactly once. Production-scale contention/load, multi-region behavior, and disaster recovery remain untested.

## Phase 1F readiness limitations

- Phase 1B lead notification/assignment/CRM/export/customer-withdrawal and distributed abuse controls remain deferred. The mortgage redirect is current legacy behavior scheduled for replacement; CRM/e-signature provider labels remain disabled.
- Borrower identity/financial/document intake is now approved under `docs/28_BORROWER_APPLICATION_MVP_REQUIREMENTS.md`. Credit-bureau connectivity, automated underwriting/approval, lender submission, deal compliance, full CRM, commissions/payroll, custom signing, automated FSRA verification, and independent agent portals remain out of scope.
- The Documenso adapter supports explicit server-side status refresh against one configured HTTPS origin and refuses redirects. Self-hosted production deployment, backup/restore, monitoring, credentials, outbound policy, deployed-version status confirmation, webhook names/signatures, reconciliation scheduling, and failure alerting remain Phase 1F or conditional deployment work. No webhook behavior is claimed.
- Production hosting/release configuration, Supabase Auth and transactional-email configuration, monitoring/error reporting, PostgreSQL/MinIO/identity-configuration backup and isolated restore drills, incident response, access/MFA/role/credential/secrets review, revocation/offboarding exercises, firewall/network review, privacy/security operations, host hardening, and release approval remain unresolved. The deployment host itself is no longer an open selection.
- Migration `20260718_0007` resolves the known general Phase 1D index/foreign-key metadata drift. That completion is not launch approval: production migration, backup, rollback, restore, and return-to-service procedures still require Phase 1F evidence and owner approval.
- Candidate migration `20260719_0008` passed blank upgrade, one-head assertion, model-schema drift check, downgrade to `20260718_0007`, and re-upgrade in an isolated PostgreSQL database on 2026-07-19. This does not prove retained production-data reconciliation, backup restore, rollout timing, or rollback safety on the future deployment host.
- Legacy review/onboarding rows whose correct application or assignment cannot be proved remain nullable and are rejected by new mutation/readiness paths. No guess-based backfill is performed; an owner-approved data reconciliation would be required if such rows exist in a retained environment.
- Linux Mint reconstruction proves local operability, not disaster recovery or portability to an untested host. A repeatable rebuild/restore drill and recorded rollback remain Phase 1F work.
- Audit events are append-oriented through application APIs, but dedicated database privileges, retention, immutable export/tamper evidence, and operational review remain production work.
- UI tests cover semantic controls, text status, focus/error/live-region behavior, duplicate actions, and responsive CSS guardrails. Genuine Firefox now covers the required 320–1920 CSS-pixel reflow set at normal zoom and three closed-tab candidate sign-ins; manual keyboard, screen-reader, contrast, reduced-motion, touch-target, zoom variation, and cross-browser review are still required. No WCAG certification is claimed.
- Owner approval/licensing remains required for the Phase 1A logo/font/photography and final public legal/regulatory presentation.

Current local-Docker operation and validation evidence is recorded in `docs/LOCAL_DEVELOPMENT.md`; historical phase evidence remains in the phase implementation reports.

- Candidate migration `20260719_0008` has two intentional stop boundaries: upgrade refuses duplicate non-null legacy provider envelope IDs, and downgrade refuses rows with provider-rejected envelope status. Neither case can be resolved automatically without selecting or relabeling evidence. An approved operator reconciliation/export procedure is required before retrying; blank and representable-data downgrade/re-upgrade remain supported.

The merged browser-completion implementation has deterministic coverage for
no-assignment stability, field guidance/`422` mapping, candidate TOTP step-up,
application-specific information requests, and authorization boundaries. The
fresh genuine candidate journey passed, including real TOTP AAL2 and owned
document metadata access. A final owner-operated administrator request ceremony
and a second genuine cross-candidate denial remain useful additional release
assurance, but neither is an uncommitted source-completion blocker or production
approval.
