# Known Limitations

Phase 1B is a reviewable lead-flow engineering implementation on top of the Phase 1A public site and Phase 0 foundation. It is not a production launch, legal approval, accessibility certification, or compliance certification.

## Product and privacy boundary

- The owner supplied the current public/legal name, `FSCO # 13696`, address, support email, phone, and secure application URL. These are controlled configuration rather than placeholders. Production still requires owner/legal confirmation of the final regulatory presentation and legal/privacy/complaints/accessibility wording.
- The approved desktop mockups now inform the implemented tokens, responsive public shell, split-image heroes, trust bands, cards, typography direction, and CTAs. No standalone approved vector logo, font files/licences, or source photography was supplied; the site therefore uses an accessible CSS/text lockup and two documented generated photography-only assets pending owner licensing/visual approval.
- Candidate registration/provisioning, applications, posting queries, review queues, onboarding workflows, controlled-document issuance, and public agent-profile queries remain for later phases. Because no candidate application submission exists yet, the required pre-submission candidate privacy disclosure also remains to be implemented with that flow.
- Agent and career landing pages show honest finished empty states. Dynamic profile/posting slugs return non-public behavior and expose no database records. Database-backed publication filtering and query tests must be implemented with Phases 1C and 1E before any records are connected.
- `/apply` now has resilient minimal submission, optional safe query attribution, the existing HTTPS/exact-host API redirect, conditional booking rendering, and a protected lead queue with marketing withdrawal. Final service/marketing/privacy wording remains explicitly draft engineering/legal-review material until owner/legal/privacy approval. No booking URL or agent redirect mapping is inferred when configuration is empty.
- Independent agent portals/microsites, mortgage origination, borrower documents, lender submissions, commissions, payroll, custom signing, automated FSRA verification, and a client CRM remain explicitly out of scope.

## Security and operations

- The public lead endpoint now has an always-on bounded process-local direct-peer limiter and a hidden-field automation trap. It rejects excess requests with `429`, fails closed when its bounded client table is full, and intentionally ignores spoofable forwarding headers. This is a safe modular-monolith foundation, not a complete production abuse platform: a multi-process or multi-replica deployment needs an approved aggregate edge/distributed control, explicit trusted-proxy topology, monitoring, and limit tuning.
- Lead notification/email, assignment, contacted/closed mutation UI, CRM synchronization, customer self-service withdrawal, and retention/deletion jobs are not implemented. The current queue is read-only apart from admin marketing-consent withdrawal; there are no bulk actions or export.
- The process-local limiter is intentionally per process. Multi-replica aggregate enforcement, trusted-proxy topology, tuning, monitoring, and abuse response remain production work.
- Queue ordering/filter indexes are issued in Alembic revision `20260714_0002`; the coordinator validated both the normal upgrade and the complete chain on an isolated empty PostgreSQL database. Each deployment still must apply the migration through its controlled workflow, and production-volume query-plan/load validation remains outstanding.
- Candidate storage has an abstraction, metadata, authorization, quarantine, and retrieval. There is no upload endpoint, magic-byte/extension validation, malware-scanner implementation, retention/deletion workflow, or R2 integration test.
- The R2 adapter and hosted Supabase JWT/JWKS path require real non-production integration testing. No provider credentials are included. Secure password reset is delegated to the future managed-identity flow; provider session revocation/offboarding integration and candidate MFA policy are not complete.
- The mortgage application integration is a validated configuration-only redirect, not an API integration. CRM and e-signature providers remain disabled adapter labels. No provider availability, timing, booking vendor, or downstream capability is claimed.
- Candidate activation does not yet evaluate mandatory onboarding gates; it must not be exposed operationally until that service exists.
- Audit events are append-oriented through application APIs, but dedicated database privileges, retention, immutable export/tamper-evidence, access review, and security-event operations remain production work.
- Retention categories exist only as policy requirements. Final periods, deletion execution, litigation/regulatory holds, and owner-approved policy are not implemented.
- Email, monitoring/error reporting, backup and isolated restore testing, incident response, secret scanning, access review, vendor/subprocessor registers, privacy/data-processing registers, vulnerability operations, and deployment hosting are unselected or unexecuted.
- Accessibility components provide semantic labels, focus, errors, reflow-oriented layout, and non-colour status text, but there has been no browser automation or manual WCAG 2.1 AA audit.
- CSS and component tests cover explicit 320px-oriented reflow guardrails, but there is not yet a cross-browser visual-regression suite or owner-approved mobile reference. Manual keyboard, zoom, screen-reader, contrast, and 320 CSS-pixel review remain required.
- Local Supabase subjects are not automatically provisioned into application users. This is intentional deny-by-default behavior, but requires a controlled, audited administration workflow.

## Dependency and environment validation

- `package-lock.json` is preserved as a lockfile v3 workspace graph. It contains registry integrity hashes, only expected local workspace links, and four reviewed packages with install scripts (`esbuild`, optional `fsevents`, `sharp`, and `unrs-resolver`).
- The lockfile pins the supported Vitest 3.2.6 security patch and overrides Next 16.2.10's nested PostCSS to patched 8.5.19; no unsafe Next downgrade is used.
- Live npm validation is complete: `npm ci` succeeded; `npm ls` confirms Vitest 3.2.6, Next 16.2.10, and PostCSS 8.5.19; all 5 frontend tests passed under Vitest 3.2.6; lint, typecheck, and the production build passed; the build generated 21 routes; and live `npm audit` reported zero vulnerabilities.
- Local Docker/PostgreSQL validation is complete: `docker compose config` passed; the API and web images built successfully; and `docker compose up -d` started healthy PostgreSQL and API services plus the web container.
- Backend `pytest` passed all 29 tests, and `alembic upgrade head` plus `alembic current` succeeded against PostgreSQL at revision `20260714_0001`.
- Hosted Supabase Auth/JWKS and R2 integration remain unverified, and the Supabase CLI is not installed. Backup/restore, deployment, and production-readiness validation also remain unexecuted; no production readiness should be inferred from the completed local checks.
