# Known Limitations

Phase 0 is a reviewable engineering foundation, not a production launch or a compliance certification.

## Product and privacy boundary

- Public content, regulatory identity, privacy, complaints, accessibility, and contact details are explicit placeholders pending owner and legal approval.
- The supplied desktop mockups informed tokens and layout direction only; pages are not final high-fidelity reproductions.
- Candidate registration/provisioning, applications, posting queries, review queues, onboarding workflows, controlled-document issuance, and public agent-profile queries remain for later phases. Because no candidate application submission exists yet, the required pre-submission candidate privacy disclosure also remains to be implemented with that flow.
- Agent and career dynamic pages render foundation text only and expose no database record. Publication filtering must be implemented and tested before real content is connected.
- Independent agent portals/microsites, mortgage origination, borrower documents, lender submissions, commissions, payroll, custom signing, automated FSRA verification, and a client CRM remain explicitly out of scope.

## Security and operations

- The public lead endpoint now has an always-on bounded process-local direct-peer limiter and a hidden-field automation trap. It rejects excess requests with `429`, fails closed when its bounded client table is full, and intentionally ignores spoofable forwarding headers. This is a safe modular-monolith foundation, not a complete production abuse platform: a multi-process or multi-replica deployment needs an approved aggregate edge/distributed control, explicit trusted-proxy topology, monitoring, and limit tuning.
- Lead notification, assignment queues, consent withdrawal, and retention/deletion jobs are not implemented.
- Candidate storage has an abstraction, metadata, authorization, quarantine, and retrieval. There is no upload endpoint, magic-byte/extension validation, malware-scanner implementation, retention/deletion workflow, or R2 integration test.
- The R2 adapter and hosted Supabase JWT/JWKS path require real non-production integration testing. No provider credentials are included. Secure password reset is delegated to the future managed-identity flow; provider session revocation/offboarding integration and candidate MFA policy are not complete.
- Mortgage application, CRM, and e-signature providers are disabled adapter/configuration boundaries. No working integration is claimed.
- Candidate activation does not yet evaluate mandatory onboarding gates; it must not be exposed operationally until that service exists.
- Audit events are append-oriented through application APIs, but dedicated database privileges, retention, immutable export/tamper-evidence, access review, and security-event operations remain production work.
- Retention categories exist only as policy requirements. Final periods, deletion execution, litigation/regulatory holds, and owner-approved policy are not implemented.
- Email, monitoring/error reporting, backup and isolated restore testing, incident response, secret scanning, access review, vendor/subprocessor registers, privacy/data-processing registers, vulnerability operations, and deployment hosting are unselected or unexecuted.
- Accessibility components provide semantic labels, focus, errors, reflow-oriented layout, and non-colour status text, but there has been no browser automation or manual WCAG 2.1 AA audit.
- Local Supabase subjects are not automatically provisioned into application users. This is intentional deny-by-default behavior, but requires a controlled, audited administration workflow.

## Dependency and environment validation

- `package-lock.json` is preserved as a lockfile v3 workspace graph. It contains registry integrity hashes, only expected local workspace links, and four reviewed packages with install scripts (`esbuild`, optional `fsevents`, `sharp`, and `unrs-resolver`).
- The lockfile pins the supported Vitest 3.2.6 security patch and overrides Next 16.2.10's nested PostCSS to patched 8.5.19; no unsafe Next downgrade is used.
- Live npm validation is complete: `npm ci` succeeded; `npm ls` confirms Vitest 3.2.6, Next 16.2.10, and PostCSS 8.5.19; all 5 frontend tests passed under Vitest 3.2.6; lint, typecheck, and the production build passed; the build generated 21 routes; and live `npm audit` reported zero vulnerabilities.
- Local Docker/PostgreSQL validation is complete: `docker compose config` passed; the API and web images built successfully; and `docker compose up -d` started healthy PostgreSQL and API services plus the web container.
- Backend `pytest` passed all 29 tests, and `alembic upgrade head` plus `alembic current` succeeded against PostgreSQL at revision `20260714_0001`.
- Hosted Supabase Auth/JWKS and R2 integration remain unverified, and the Supabase CLI is not installed. Backup/restore, deployment, and production-readiness validation also remain unexecuted; no production readiness should be inferred from the completed local checks.
