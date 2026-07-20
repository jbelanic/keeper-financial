# Phase 1F Production and Controlled-Pilot Readiness Plan

- **Status:** Draft for owner decisions and approval
- **Date:** 2026-07-19
- **Source branch:** `feat/admin-workflow-operator-ux`
- **Source baseline:** owner-accepted administrator/operator commit `17e1b43`, integrated for publication with local `main` content commit `07895c2`; both descend from `3331519`
- **Candidate migration head:** `20260719_0008`
- **Authority:** `AGENTS.md`, `docs/00_PROJECT_SOURCE_OF_TRUTH.md`, approved decisions in `docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md`, and the current architecture, security, lifecycle, delivery, API/data, test, limitations, and implementation-evidence documents

## 1. Purpose and approval boundary

This document defines the evidence, decisions, procedures, stop conditions, recovery boundaries, and release gates required before a controlled pilot or production operation may be approved. It is planning and evidence definition only.

This plan does **not itself** authorize:

- Phase 1F implementation;
- commit, push, pull request, merge, or history rewriting;
- deployment or shared-database migration;
- use of production or pilot credentials;
- changes to firewall rules, DNS, certificates, services, vendors, or external systems;
- processing of real candidate or borrower data;
- final candidate activation, candidate-to-agent transition, or agent-role grant;
- legal, privacy, regulatory, claims, accessibility, controlled-pilot, or production approval;
- destructive, rollback, restore, deletion, credential-rotation, or incident actions.

No Codex or other implementation agent may execute Phase 1F work from this draft. Before implementation, the owner must approve the plan, evidence requirements, owner decisions, scope, and acceptance criteria through repository change control and separately authorize any Git publication or operational action.

## 2. Governing boundaries

The following boundaries remain mandatory throughout readiness work:

1. The application remains a brokerage relationship platform, not a mortgage origination, underwriting, lender-submission, commission, payroll, or borrower-document system.
2. Supabase Auth proves identity only. PostgreSQL relationships, roles, lifecycle, ownership, and resource authorization remain authoritative.
3. Generic sign-in remains non-provisioning. Only the posting-bound application-start boundary may create or reuse the approved candidate relationships.
4. MinIO remains the only application object store. Supabase Storage and its S3 protocol remain disabled.
5. ClamAV validation remains fail closed before private-object persistence.
6. Self-hosted Documenso remains an external provider boundary. The application does not implement custom signing or claim legal validity from a checkbox or typed name.
7. `activation_ready` remains a calculation only. Readiness work must not add or simulate final activation, candidate-to-agent transition, or agent-role grant.
8. Full borrower applications and associated financial, underwriting, identity, and lender-submission data remain in approved external mortgage systems.
9. No unresolved legal, privacy, regulatory, claims, accessibility, vendor, retention, deployment, or data-boundary decision may be converted into an engineering assumption.
10. Evidence must use synthetic or explicitly approved data, omit secrets and tokens, minimize personal information, and identify the exact environment and source revision.

## 3. Evidence status vocabulary

Each readiness item and final evidence manifest must use exactly one status:

- **Accepted source:** owner-accepted implementation evidence; not operational approval.
- **Planned:** procedure and evidence definition exist, but execution is not authorized or complete.
- **Blocked — owner decision:** a material decision or named owner is missing.
- **Blocked — review:** privacy, legal, regulatory, claims, security, or accessibility review is incomplete.
- **Failed:** execution occurred under separate authorization and a pass criterion was not met.
- **Passed for controlled pilot:** pilot evidence passed but production evidence may remain.
- **Passed for production:** production evidence passed and the designated approvers accepted it.
- **Not applicable by approved scope:** the owner explicitly excluded the item and documented why exclusion does not weaken another gate.

Passing tests or a successful local ceremony alone never changes an item to pilot- or production-approved.

## 4. Confirmed owner-accepted implementation

The following source implementation is accepted. These facts define the starting point; they are not substitutes for the operational evidence in Section 7.

### 4.1 Identity, authorization, and data boundaries

- Supabase identity is separated from application authorization.
- Posting-bound registration and sign-in use the dedicated narrow provisioning boundary; generic sign-in remains non-provisioning.
- Candidate and administrator TOTP/AAL2 paths exist, with application-database role, lifecycle, ownership, and resource checks remaining authoritative.
- Candidate files use strict format/structure checks, fail-closed ClamAV scanning, and private MinIO persistence.
- Full borrower application, underwriting, lender-submission, borrower-document, commission, and payroll data remain out of scope.

### 4.2 Administrator/operator workflow boundaries

- Onboarding assignment targets one exact `CandidateApplication` attempt.
- Assignment attempts serialize on the candidate row across different applications and plans, preserving the documented application/candidate/plan lock order and leaving one active assignment.
- Unused onboarding plans may be edited, including ordered task definitions; first assignment makes plan content and availability permanently immutable.
- Gate, policy-acknowledgement, task, readiness, and e-sign evidence retain exact-assignment provenance.
- Manual administration is limited to exactly `background_check`, `fsra_authorization`, and `system_provisioning`.
- `policy_acknowledgement` and `executed_agreements` are derived-only and reject manual satisfaction or reopening.
- Manual gate correction requires a reason and append-oriented evidence; readiness remains exact-assignment and does not cross generations.
- Documenso reconciliation is provider-authoritative.
- Provider/network ambiguity and unrepresentable `DRAFT` state fail closed and leave executed-agreement readiness unsatisfied.
- Rejected envelopes may be replaced while predecessor history remains preserved and non-satisfying.
- Documenso uses one exact HTTPS `/api/v2` origin, a separately constrained public HTTPS origin, and redirect refusal.
- Agent-profile creation uses server-projected eligible active agent relationships.
- First publication permanently locks and reserves the public slug, including after unpublishing.
- `/admin/content` is removed; public content remains typed and repository-controlled.
- No final activation operation, candidate-to-agent transition, or agent-role grant exists.

### 4.3 Migration `20260719_0008`

The accepted candidate migration advances only from issued revision `20260718_0007` and intentionally:

- refuses duplicate non-null legacy provider envelope IDs before upgrade DDL;
- derives historical first-publication slug locks from authoritative profile state, publication timestamps, or `agent_profile.published` audit evidence;
- refuses downgrade before DDL when rejected-envelope evidence cannot be represented by revision `0007` without falsification;
- does not guess ambiguous legacy assignment provenance into satisfying evidence.

These stop boundaries require an owner-approved reconciliation or evidence-export procedure if encountered. They must not be bypassed, relabelled, or silently deduplicated.

### 4.4 Accepted source verification record

The accepted implementation report records:

- complete API test-directory execution with exit status `0`; no exact API passed-test count is asserted here;
- API Ruff passing;
- API mypy passing across 56 source files;
- root web tests with 142 passed and 3 skipped;
- root lint passing with zero warnings;
- root typecheck passing;
- production Next.js build passing with 35 generated pages and no `/admin/content` route;
- isolated PostgreSQL migration/concurrency suite with 10 passing tests;
- real PostgreSQL races for concurrent assignment, concurrent manual-gate satisfaction, and delayed Documenso completion versus replacement;
- deterministic OpenAPI and generated TypeScript regeneration;
- one recorded Alembic head, `20260719_0008`;
- `git diff --check` passing.

The API-suite warnings recorded at acceptance concerned Starlette `TestClient` and Alembic configuration deprecations; they were not test failures. Deprecation remediation must be tracked separately and must not be misreported as either a failed accepted suite or as operational readiness evidence.

## 5. Operational evidence still required

No item below is currently marked passed for pilot or production merely because source tests passed.

- Host, service, firewall, ingress, TLS, and exposure evidence on the intended operating host.
- Supabase Studio local-only proof and repeated proof that Storage and its S3 protocol remain disabled.
- MinIO durability, private policy, signed access, backup, retention, restore, and orphan-reconciliation evidence.
- ClamAV signature-age, update, health, alert, failure, and fail-closed exercises.
- Named access, secrets, credential, MFA, revocation, and offboarding controls.
- Approved production Auth and transactional-email configuration and exercises.
- Approved self-hosted Documenso version/topology, credentials, HTTPS routing, backup/restore, monitoring, reconciliation procedure, and runbook.
- Logging and PII-redaction review across application and infrastructure logs.
- Approved retention, deletion, correction, export, legal-hold, and end-of-pilot procedures.
- Incident response, stop, rollback, recovery, return-to-service, and escalation exercises.
- Monitoring, synthetic checks, alert routing, alert tests, and named ownership.
- Approved deployment architecture details and environment guardrails beyond the accepted local-container baseline.
- Database backup, migration preflight, rollback/restore, retained-data, and revision `0008` stop-boundary procedures.
- Genuine authenticated browser ceremonies for administrator MFA, exact-application assignment, gate correction, Documenso refresh/replacement, and profile publication.
- Privacy, legal, regulatory, claims, content/licensing, and accessibility reviews.
- Approved pilot purpose, roster, eligibility, support, data boundary, duration, stop criteria, and evidence package.

## 6. Owner-decision register

All entries are unresolved unless an approved repository decision cites the decision ID. The `Owner` field in every readiness item remains unassigned until `OD-01` is resolved; role descriptions identify required competence, not a person or approved assignment.

| ID      | Material owner decision required                                                                                                                                                                                                                                                             | Why it is required                                                                                                                       | Blocks                                              |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `OD-01` | Name the accountable Phase 1F owner, controlled-pilot decision maker, production decision maker, security reviewer, privacy/legal/regulatory reviewers, accessibility reviewer, infrastructure operator, database operator, support lead, and incident commander or approved combined roles. | Evidence cannot be accepted or escalated without named accountability and separation appropriate to risk.                                | Both                                                |
| `OD-02` | Approve the controlled pilot's purpose, scope, duration, roster, eligibility, permitted actions, excluded actions, support hours, and success measures.                                                                                                                                      | “Controlled pilot” otherwise has no bounded operating definition.                                                                        | Controlled pilot                                    |
| `OD-03` | Decide whether pilot evidence and operation use synthetic-only data or approved real personal data; identify the lawful/approved data basis and prohibited data classes.                                                                                                                     | Current authority does not permit real candidate or borrower data processing.                                                            | Both                                                |
| `OD-04` | Approve exact host ingress, DNS, TLS termination, certificate custody/renewal, trusted proxy behavior, firewall policy, remote-administration path, and whether any service is reachable beyond the host.                                                                                    | The local-container baseline does not define safe production ingress or administration. No topology may be invented.                     | Both                                                |
| `OD-05` | Decide whether the upstream development-oriented local Supabase CLI stack is accepted for controlled pilot and/or production, subject to documented compensating controls, or whether a separately approved architecture change is required.                                                 | The current code requires Supabase semantics, but upstream local tooling is not production-hardened and has broad port-binding concerns. | Both                                                |
| `OD-06` | Select and approve the transactional-email provider/configuration, sender identity, domain authentication, invitation/recovery templates, delivery monitoring, bounce handling, and support process.                                                                                         | Mailpit is capture-only and cannot provide real delivery. No vendor may be invented.                                                     | Both                                                |
| `OD-07` | Approve secrets custody, authorized custodians, generation, distribution, rotation intervals/triggers, emergency access, recovery, and evidence-redaction policy.                                                                                                                            | Current ignored local credentials are not an approved operational secrets process.                                                       | Both                                                |
| `OD-08` | Approve the exact self-hosted Documenso version, hosting boundary, API and public HTTPS origins, certificate/outbound policy, credential custody, backup/restore target, reconciliation schedule, replacement/void semantics, and whether webhooks are excluded or separately specified.     | Runtime compatibility and webhook behavior cannot be inferred from documentation or the adapter.                                         | Both                                                |
| `OD-09` | Approve backup scope, frequency, retention, encryption, storage location, access, recovery-point objective, recovery-time objective, and destruction policy for PostgreSQL, MinIO, Supabase Auth configuration/data, Documenso, and required host configuration.                             | Restore pass/fail criteria require approved objectives and destinations.                                                                 | Both                                                |
| `OD-10` | Approve retention periods and triggering events for leads, candidate drafts/applications/documents, onboarding evidence, e-sign references, agent records, consents, audit events, logs, backups, security incidents, and pilot closure.                                                     | No legal retention periods may be invented or hard-coded.                                                                                | Both                                                |
| `OD-11` | Approve deletion, correction, access/export, legal-hold, complaint, consent-withdrawal, and end-of-pilot authorities and response targets.                                                                                                                                                   | Operational procedures can otherwise delete evidence improperly or fail data-subject obligations.                                        | Both                                                |
| `OD-12` | Approve monitoring tools, storage destinations, data minimization, log retention, alert channels, on-call coverage, escalation path, and availability/security objectives.                                                                                                                   | No monitoring vendor, destination, threshold, or person may be invented.                                                                 | Both                                                |
| `OD-13` | Approve incident severity definitions, stop triggers, communication authority, evidence preservation, rollback authority, return-to-service authority, and required notifications/advisors.                                                                                                  | Operators need explicit authority before stopping or restoring service.                                                                  | Both                                                |
| `OD-14` | Approve the retained-data migration strategy and who may resolve revision `0008` duplicate-envelope upgrade or rejected-envelope downgrade stop conditions.                                                                                                                                  | The migration correctly refuses ambiguous or lossy operations; remediation is an owner/data-governance decision.                         | Both                                                |
| `OD-15` | Identify required privacy, legal, Ontario regulatory, advertising/claims, complaints/consent, public-content/licensing, and accessibility approvers and the exact approval artifacts they must issue.                                                                                        | Engineering cannot manufacture legal or regulatory conclusions or accessibility certification.                                           | Both                                                |
| `OD-16` | Approve the accessibility conformance target and review scope, including browser/assistive-technology coverage, manual review, defect severity, and accepted exceptions.                                                                                                                     | “Practical WCAG 2.1 AA expectations” does not itself define final approval evidence or exception authority.                              | Both                                                |
| `OD-17` | Approve the pilot support model, intake channel, response/escalation targets, operator coverage, candidate/administrator communications, and out-of-hours stop procedure.                                                                                                                    | A pilot cannot be controlled without reachable support and escalation ownership.                                                         | Controlled pilot                                    |
| `OD-18` | Approve public profile/regulatory content, image/font/logo licensing, principal-broker identity/title, and any claims exposed during pilot or production.                                                                                                                                    | Current implementation and source acceptance are not content, licensing, claims, or regulatory approval.                                 | Both                                                |
| `OD-19` | Decide whether manual Documenso reconciliation is sufficient for the bounded pilot or whether separately specified scheduling/webhook work is required before pilot.                                                                                                                         | No webhook name, signature, retry, or deployed-version behavior is currently approved or implemented.                                    | Controlled pilot; production decision also required |

## 7. Readiness work packages

### `RF-01` — Readiness governance and evidence control

- **Objective:** Establish an approved, traceable evidence process that separates source acceptance, operational execution, review, and owner go/no-go decisions.
- **Owner:** Unassigned. `OD-01` must name the accountable Phase 1F owner and evidence custodian.
- **Prerequisite owner decisions:** `OD-01`, `OD-02`, `OD-03`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-01-evidence-manifest.md`, containing source revision, environment identifier, execution date/time, executor, reviewer, artifact hashes where appropriate, result, deviations, and approval references. Secret or personal values must not appear.
- **Execution procedure or future runbook:** Define evidence naming, storage, redaction, review, expiry, and re-run rules. Every later artifact must link to this manifest and identify whether it is synthetic, pilot, or production evidence. Record deprecation warnings separately from failures.
- **Pass/fail criterion:** Pass only when all required roles are named, the evidence template is approved, every required work package has an entry, and no artifact contains secrets, tokens, cookies, private URLs, raw payloads, or unnecessary personal data.
- **Stop condition:** Missing owner, unverifiable environment/revision, secret/PII exposure, evidence produced from the primary checkout or another branch, or an attempt to treat source tests as release approval.
- **Rollback or recovery boundary:** Quarantine an unsafe artifact, revoke access if exposure occurred, follow the approved incident process, regenerate sanitized evidence, and retain only the approved record. Do not rewrite an audit/history record to hide the incident.
- **Blocks:** Both.

### `RF-02` — Supabase Studio local-only enforcement

- **Objective:** Prove Studio is optional operator tooling reachable only through the approved local administration boundary and is not public, shared, or application-facing.
- **Owner:** Unassigned. `OD-01` must name an infrastructure operator and security reviewer.
- **Prerequisite owner decisions:** `OD-01`, `OD-04`, `OD-05`, `OD-12`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-02-supabase-studio-exposure.md` with sanitized listener inventory, firewall policy reference, local success probe, untrusted-network denial probe, and application dependency review.
- **Execution procedure or future runbook:** On the authorized host, capture the Supabase listener/process inventory without credentials; prove local operator access; probe from the approved untrusted test point; confirm no reverse proxy, ingress, DNS, or application route exposes Studio; disable Studio when it is not operationally required if the approved topology permits that action.
- **Pass/fail criterion:** Pass only if Studio is absent or accessible solely through the owner-approved local administration path, untrusted access fails, application health is independent of Studio, and alert/review procedures cover exposure drift.
- **Stop condition:** Studio binds or routes to an unapproved interface, is reachable from an untrusted network, requires public exposure to operate, or the exact administration path has not been approved.
- **Rollback or recovery boundary:** Remove unapproved routing or stop Studio under the approved runbook, preserve Auth/application availability, investigate exposure, rotate affected credentials only under separate authority, and re-run the proof before service return.
- **Blocks:** Both.

### `RF-03` — Supabase Storage and S3 protocol disabled

- **Objective:** Prove Supabase Storage and its S3 protocol remain disabled in tracked configuration and the running environment, and that all application objects use private MinIO.
- **Owner:** Unassigned. `OD-01` must name an infrastructure operator and application security reviewer.
- **Prerequisite owner decisions:** `OD-01`, `OD-04`, `OD-05`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-03-supabase-storage-disabled.md` with sanitized tracked-config excerpts, rendered/runtime service inventory, negative endpoint probes, and application storage configuration evidence.
- **Execution procedure or future runbook:** Verify `[storage].enabled = false` and `[storage.s3_protocol].enabled = false`; inspect the runtime inventory for absent Storage/S3 services and routes; prove the API uses `STORAGE_BACKEND=s3` with the approved MinIO endpoint/bucket; perform an approved private-object upload/download ceremony through the application rather than enabling Supabase Storage.
- **Pass/fail criterion:** Pass only when both Supabase features are disabled in source and runtime, negative probes fail safely, MinIO remains the sole object store, and no object metadata or bytes are found in a Supabase Storage path.
- **Stop condition:** Either feature is enabled, a Storage/S3 route responds as active, application configuration points at Supabase Storage, or proof would require exposing credentials.
- **Rollback or recovery boundary:** Stop application writes, restore the approved disabled configuration under separate change authority, inventory any misplaced objects without copying them into evidence, reconcile under an approved data procedure, and repeat the proof.
- **Blocks:** Both.

### `RF-04` — MinIO persistence, privacy, backup, retention, and isolated restore

- **Objective:** Demonstrate durable private object storage, policy enforcement, backup completeness, approved retention handling, and isolated restore without public exposure or orphaned metadata.
- **Owner:** Unassigned. `OD-01` must name an infrastructure/storage operator, database operator, privacy reviewer, and independent restore witness.
- **Prerequisite owner decisions:** `OD-01`, `OD-03`, `OD-07`, `OD-09`, `OD-10`, `OD-11`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-04-minio-backup-restore.md` plus an approved restore manifest containing synthetic object IDs/hashes, PostgreSQL metadata references, backup timestamp, restore target, and recovery measurements. Do not record object keys or signed URLs beyond the restricted evidence boundary.
- **Execution procedure or future runbook:** Verify named-volume persistence across restart; prove anonymous access is denied; validate short-lived authorized download and cross-user denial; create a coordinated PostgreSQL/MinIO backup at an approved consistency boundary; restore into an isolated target with no production ingress; reconcile metadata-to-object and object-to-metadata orphans; test approved retention/legal-hold exclusions; destroy the isolated target only under the approved evidence-destruction procedure.
- **Pass/fail criterion:** Pass when all expected synthetic objects and metadata restore consistently, hashes match, unauthorized/public access fails, signed access expires as designed, no unexplained orphan exists, recovery objectives from `OD-09` are met, and retention/legal-hold rules are demonstrably enforced.
- **Stop condition:** Missing or inconsistent backup, public/anonymous access, checksum mismatch, orphaned data without approved disposition, restore into a shared/live target, unresolved retention authority, or recovery-objective breach.
- **Rollback or recovery boundary:** Keep the live source read-only or stopped as defined by the incident runbook; do not overwrite it with an unverified restore. Preserve failed restore evidence, correct the procedure under change control, and repeat in a fresh isolated target.
- **Blocks:** Both.

### `RF-05` — ClamAV freshness, monitoring, alerting, and fail-closed operation

- **Objective:** Prove current signature management, daemon health, alert routing, and application fail-closed behavior without persisting unsafe or unscanned bytes.
- **Owner:** Unassigned. `OD-01` must name an infrastructure/security operator and alert recipient.
- **Prerequisite owner decisions:** `OD-01`, `OD-09`, `OD-12`, `OD-13`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-05-clamav-readiness.md` with engine/signature version and age, update status, health history, safe in-memory clean/detection verifier result, alert-test record, and application failure exercise.
- **Execution procedure or future runbook:** Define maximum approved signature age and update-failure threshold; monitor FreshClam and clamd health; run the repository in-memory clean/detection verifier; exercise daemon unavailable, timeout, malformed response, and non-clean result through an authorized synthetic AAL2 upload path; prove no MinIO bytes or PostgreSQL document metadata are created on failure.
- **Pass/fail criterion:** Pass when signatures are within the approved age, update and health alerts reach the named recipient, clean and detection samples produce expected bounded results, all scanner failures return safe failure and persist nothing, and port `3310` remains internal/loopback-only.
- **Stop condition:** Stale or unknown signatures, update failure beyond approved threshold, untested or broken alerting, scanner bypass/fallback, public clamd exposure, false success, or persisted bytes/metadata after scan failure.
- **Rollback or recovery boundary:** Stop document acceptance, keep existing private objects governed by normal authorization, restore scanner health/signatures under the runbook, investigate possible exposure, and re-run all fail-closed evidence before reopening uploads.
- **Blocks:** Both.

### `RF-06` — Firewall, service binding, ingress, and network exposure

- **Objective:** Prove every listener, ingress route, trusted proxy, outbound path, and administration path matches an approved topology and exposes no internal service unintentionally.
- **Owner:** Unassigned. `OD-01` must name a host/network operator and independent security reviewer.
- **Prerequisite owner decisions:** `OD-01`, `OD-04`, `OD-05`, `OD-08`, `OD-12`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-06-network-exposure.md` containing the approved data-flow diagram, sanitized listener inventory, firewall ruleset reference, local/remote probe matrix, DNS/TLS certificate evidence, trusted-proxy findings, and outbound allow-list evidence.
- **Execution procedure or future runbook:** Enumerate host and container listeners; map each to an approved purpose; validate loopback bindings for PostgreSQL, MinIO console/API, clamd, API, web, and local operator tools where required; test from local, trusted administration, pilot-client, and untrusted test points; verify TLS and certificate renewal for approved HTTPS ingress; confirm Documenso outbound requests can reach only the approved origin and do not follow redirects.
- **Pass/fail criterion:** Pass when every reachable port and route has explicit approval, internal services fail from untrusted networks, only approved ingress is reachable, TLS and trusted-proxy behavior pass, outbound restrictions match the Documenso/mortgage-provider allow-lists, and exposure drift is monitored.
- **Stop condition:** Unknown listener, broad Supabase/Studio/MinIO/PostgreSQL/clamd exposure, unapproved reverse proxy, wildcard ingress/CORS, invalid certificate, trusted-header spoofing, unrestricted sensitive outbound traffic, or missing topology decision.
- **Rollback or recovery boundary:** Remove unapproved ingress or stop the affected service under incident authority, preserve evidence, assess credential/data exposure, and require a clean re-probe before return to service.
- **Blocks:** Both.

### `RF-07` — Secrets, credentials, MFA, roles, access review, revocation, and offboarding

- **Objective:** Establish least-privilege credential custody and prove that access is granted, reviewed, revoked, and offboarded without relying on identity alone.
- **Owner:** Unassigned. `OD-01` must name a security owner, identity operator, application/database access reviewer, and incident approver.
- **Prerequisite owner decisions:** `OD-01`, `OD-03`, `OD-05`, `OD-07`, `OD-12`, `OD-13`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-07-access-and-secrets.md` with a redacted credential inventory, role/access matrix, named access-review sign-off, MFA enrollment/recovery evidence, revocation/offboarding exercise, break-glass record, and confirmation that no secret entered source, logs, screenshots, or browser-visible variables.
- **Execution procedure or future runbook:** Inventory credential classes and custodians; separate browser-safe anon key from privileged material; confirm admin AAL2 and server-side role/lifecycle checks; review all application roles and local identities; exercise session revocation, user deactivation, role removal, and offboarding; verify suspended/offboarded users lose access on fresh and existing sessions; define emergency access and rotation triggers without printing secret values.
- **Pass/fail criterion:** Pass when every credential and privileged role has a named owner and least-privilege purpose, no default or `change-me` value remains, administrator access requires AAL2 plus active database authorization, revocation/offboarding meets approved timing, and evidence contains no secret material.
- **Stop condition:** Unknown credential owner, shared/unreviewed privileged account, missing admin MFA, identity-only access, failed revocation, genuine subject overwritten by local linking, service-role use in browser or linking, or secret leakage.
- **Rollback or recovery boundary:** Disable affected access under incident authority, rotate only through the approved secrets runbook, invalidate sessions, preserve audit evidence, and re-run access review before restoration.
- **Blocks:** Both.

### `RF-08` — Production Supabase Auth and transactional email

- **Objective:** Prove the approved identity/email configuration supports secure confirmation, invitation where used, recovery, session refresh/revocation, delivery, and offboarding without granting application access automatically.
- **Owner:** Unassigned. `OD-01` must name identity, email, security, privacy, and support owners.
- **Prerequisite owner decisions:** `OD-01`, `OD-03`, `OD-05`, `OD-06`, `OD-07`, `OD-11`, `OD-17`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-08-auth-email.md` with approved configuration manifest, sender/domain-authentication evidence, synthetic confirmation/recovery/revocation journeys, delivery/bounce evidence, session-expiry results, and privacy-reviewed templates. No links, codes, tokens, cookies, or addresses beyond approved synthetic identifiers may be recorded.
- **Execution procedure or future runbook:** Deploy only the approved Auth/email topology; verify exact callback allow-lists, ES256/JWKS issuer/audience behavior, password/MFA settings, sender authentication, and template wording; run posting-bound registration and existing-user recovery; prove generic sign-in remains non-provisioning; exercise refresh, expiry, revocation, password reset, failed delivery, bounce, and offboarding support paths.
- **Pass/fail criterion:** Pass when approved messages deliver through the selected provider, callbacks stay on exact allow-lists, tokens never enter logs/URLs/evidence, generic sign-in grants no local access, mapped access still requires active application authorization, and recovery/revocation/offboarding meet approved targets.
- **Stop condition:** No approved provider/topology, Mailpit mistaken for delivery, callback/origin drift, unsigned or wrong-issuer tokens accepted, user metadata treated as verification, service credential exposed, failed revocation, or unapproved message wording.
- **Rollback or recovery boundary:** Stop sign-up/recovery or affected portal access as defined by the incident plan, revoke sessions/credentials under authority, restore the last approved configuration, and re-run the complete journey before reopening.
- **Blocks:** Both.

### `RF-09` — Self-hosted Documenso operational readiness

- **Objective:** Prove the exact approved Documenso deployment and operator process produce authoritative, recoverable, monitored e-sign evidence without custom signing claims or unsafe network behavior.
- **Owner:** Unassigned. `OD-01` must name the Documenso operator, security reviewer, backup operator, legal/privacy reviewer, and onboarding process owner.
- **Prerequisite owner decisions:** `OD-01`, `OD-03`, `OD-04`, `OD-07`, `OD-08`, `OD-09`, `OD-10`, `OD-12`, `OD-15`, `OD-19`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-09-documenso-readiness.md` with exact version, API compatibility record, approved origins, certificate evidence, redacted credential custody, backup/restore proof, monitoring/alert test, reconciliation schedule, status mapping, failure/replacement ceremony, and operator runbook approval.
- **Execution procedure or future runbook:** Verify the deployed version against the exact API endpoint/status contract; configure one exact HTTPS `/api/v2` origin and approved public HTTPS origin; deny redirects and non-HTTPS; exercise `PENDING`, `COMPLETED`, `REJECTED`, unavailable/malformed, and `DRAFT` handling; replace a rejected envelope while preserving predecessor history; restore Documenso in isolation and reconcile application references; define manual/scheduled reconciliation. Do not implement or claim webhook behavior unless `OD-08` and a separate approved specification define exact names, signatures, retries, ordering, and replay handling.
- **Pass/fail criterion:** Pass when provider identity/status is verified, only provider-confirmed completion satisfies the derived gate, unavailable/ambiguous/`DRAFT` responses fail closed, rejected replacement preserves history, redirects/non-HTTPS fail, credentials remain secret, backup/restore meets objectives, and alerts/runbook reach named owners.
- **Stop condition:** Unknown/unapproved version, API mismatch, HTTP or redirect acceptance, provider ambiguity producing readiness, predecessor mutation/deletion, missing backup, unapproved webhook assumptions, token/body leakage, or legal/privacy review missing.
- **Rollback or recovery boundary:** Stop new envelope linking/reconciliation, force executed-agreement readiness unsatisfied where current verification is unavailable, preserve historical rows, restore the approved provider/configuration, reconcile under the runbook, and never relabel evidence to make an older revision fit.
- **Blocks:** Both because the required pilot ceremonies include provider refresh/replacement. A narrower pilot exclusion would require explicit owner approval and must leave executed agreements unsatisfied.

### `RF-10` — Logging, audit evidence, and PII safety

- **Objective:** Prove application and infrastructure logs are useful for operations while excluding tokens, secrets, private URLs, document contents, raw payloads, and unnecessary personal data; preserve distinct append-oriented audit evidence.
- **Owner:** Unassigned. `OD-01` must name application, infrastructure, security, and privacy reviewers.
- **Prerequisite owner decisions:** `OD-01`, `OD-03`, `OD-10`, `OD-11`, `OD-12`, `OD-15`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-10-logging-pii-review.md` with data-flow inventory, sampled/redacted log review, prohibited-field probes, audit/log separation, access/retention controls, export procedure, and reviewer sign-offs.
- **Execution procedure or future runbook:** Generate approved synthetic auth, application, upload, gate, e-sign, publication, error, and incident events; inspect web/API/PostgreSQL/MinIO/ClamAV/Supabase/Documenso/proxy logs and audit records; verify request IDs and safe identifiers support correlation; test redaction and error handling; confirm log access and retention follow approved policy.
- **Pass/fail criterion:** Pass when prohibited data is absent, errors remain diagnosable through safe categories/request IDs, audit events retain required actor/target/status evidence, access is least privilege, and retention/export meet approved policy.
- **Stop condition:** Token, cookie, reset/confirmation link, secret, document content, raw form payload, private object URL, sensitive free text, or unapproved personal data appears; audit history is editable by ordinary operators; or log destination/retention is unapproved.
- **Rollback or recovery boundary:** Stop affected logging/export, restrict access, preserve incident evidence, rotate exposed credentials under authority, purge only under approved legal/retention direction, repair redaction, and repeat the probe.
- **Blocks:** Both.

### `RF-11` — Retention, deletion, correction, export, legal hold, and pilot closure

- **Objective:** Establish approved lifecycle procedures for every retained data class without fabricating periods or erasing required evidence.
- **Owner:** Unassigned. `OD-01` must name privacy/legal, records, database, object-storage, application, and support owners.
- **Prerequisite owner decisions:** `OD-01`, `OD-03`, `OD-09`, `OD-10`, `OD-11`, `OD-15`, `OD-17`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-11-data-lifecycle.md` with approved retention schedule, data inventory, trigger matrix, legal-hold procedure, correction/export/deletion tests using synthetic data, backup propagation rules, and end-of-pilot checklist.
- **Execution procedure or future runbook:** Map each PostgreSQL, MinIO, Supabase Auth, Documenso reference, audit, log, and backup record to an approved category; define lifecycle triggers and holds; exercise identity verification for requests; export only approved fields; correct without rewriting immutable history; delete/de-identify only under authority; prove held data is excluded; reconcile metadata/objects/backups; close a synthetic pilot participant.
- **Pass/fail criterion:** Pass when all data classes have approved periods/triggers/owners, request procedures are authenticated and auditable, immutable evidence remains accurate, holds prevent deletion, exports exclude internal/restricted fields unless approved, and pilot closure meets the approved schedule.
- **Stop condition:** Missing retention decision, ambiguous authority, borrower data discovered, deletion would falsify evidence, hold conflict, uncontrolled backup copies, or export leaks internal notes/secrets/other-subject data.
- **Rollback or recovery boundary:** Pause lifecycle action, preserve data and legal hold, restore only from an approved backup if an authorized deletion/correction failed, record the incident, and retry only after privacy/legal direction.
- **Blocks:** Both.

### `RF-12` — Incident response, stop criteria, rollback, and return to service

- **Objective:** Provide an exercised decision path for containment, evidence preservation, recovery, communication, and controlled return to service.
- **Owner:** Unassigned. `OD-01` and `OD-13` must name the incident commander, alternates, technical responders, communications authority, and return-to-service approver.
- **Prerequisite owner decisions:** `OD-01`, `OD-09`, `OD-11`, `OD-12`, `OD-13`, `OD-15`, `OD-17`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-12-incident-exercise.md` plus approved incident runbook, contact/escalation matrix, scenario records, decision log, recovery validation, and return-to-service sign-off.
- **Execution procedure or future runbook:** Define severity and stop thresholds; tabletop and technically exercise at minimum credential exposure, unauthorized admin access, public object exposure, stale/unavailable scanner, failed backup/restore, migration refusal/failure, Documenso ambiguity, email/Auth outage, PII in logs, and host/network compromise; record who may stop writes/services, preserve evidence, notify advisors/users, roll back, restore, and approve return.
- **Pass/fail criterion:** Pass when named responders receive alerts, make decisions within approved targets, containment prevents further unsafe writes/access, evidence is preserved safely, recovery follows verified backups/runbooks, and independent return-to-service checks pass.
- **Stop condition:** Missing authority/contact, uncertain data exposure, no clean restore, failed containment, unresolved scanner/Auth/authorization/PII issue, or pressure to return without required approval.
- **Rollback or recovery boundary:** Scenario-specific and owner-approved; no generic destructive rollback is authorized. Prefer stop/read-only isolation, preserve immutable evidence, restore into isolation, validate, then return only after named approval.
- **Blocks:** Both.

### `RF-13` — Monitoring, synthetic checks, alert tests, escalation, and ownership

- **Objective:** Detect availability, security, freshness, capacity, and workflow failures early and route actionable alerts to named owners without collecting prohibited data.
- **Owner:** Unassigned. `OD-01` and `OD-12` must name service owners, on-call coverage, escalation recipients, and alert reviewers.
- **Prerequisite owner decisions:** `OD-01`, `OD-09`, `OD-12`, `OD-13`, `OD-17`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-13-monitoring-alerts.md` with service-level inventory, approved thresholds, synthetic-check definitions, alert routing, alert-test results, escalation timing, dashboard access, and data-minimization review.
- **Execution procedure or future runbook:** Monitor host resources, container/process state, PostgreSQL, MinIO, bucket privacy, ClamAV freshness/health, API `/health` and `/health/db`, web routes, Supabase Auth/JWKS, email delivery, Documenso reconciliation, certificate expiry, backup completion, restore-test age, failed logins/MFA, authorization denials, upload failures, migration revision, and evidence-job freshness. Run synthetic checks with dedicated approved accounts/data and no final activation.
- **Pass/fail criterion:** Pass when every critical dependency and security control has an owner-approved signal/threshold, test alerts reach primary and escalation recipients, false/duplicate alert handling is documented, dashboards are least privilege, and synthetic data cannot create real candidate/agent state.
- **Stop condition:** Critical blind spot, alert not delivered, unknown owner, synthetic check changes real data or grants a role, monitoring stores prohibited PII/secrets, or stale backup/certificate/signature condition is ignored.
- **Rollback or recovery boundary:** Disable only the unsafe synthetic check, not the underlying safety control; restore monitoring from approved configuration, investigate missed alerts, and repeat alert tests before go/no-go.
- **Blocks:** Both.

### `RF-14` — Deployment architecture and environment guardrails

- **Objective:** Convert the approved local Linux Docker baseline into an explicit, reproducible, fail-closed pilot/production operating specification without introducing unapproved infrastructure.
- **Owner:** Unassigned. `OD-01` must name architecture, infrastructure, security, and operations approvers.
- **Prerequisite owner decisions:** `OD-01`, `OD-04`, `OD-05`, `OD-07`, `OD-08`, `OD-09`, `OD-12`, `OD-13`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-14-deployment-guardrails.md` with approved topology/data-flow diagrams, image/version inventory, configuration manifest with values redacted, rendered Compose check, host baseline, startup/shutdown order, dependency health, rebuild procedure, and drift review.
- **Execution procedure or future runbook:** Pin and review service/image versions; define host prerequisites and patching; render configuration from a sanitized reference; prove production validation rejects debug, dev auth, local files, public objects, wildcard/remote origins, wrong database/storage/scanner hosts, disabled MFA, and non-fail-closed scanning; define explicit migration-before-app startup; reconstruct on an isolated host/target; compare runtime to approved topology.
- **Pass/fail criterion:** Pass when reconstruction is repeatable, every dependency becomes healthy in approved order, migration remains explicit, configuration fails closed on every prohibited setting, runtime matches the approved topology, no unapproved cloud/service key exists, and drift is detectable.
- **Stop condition:** Unpinned/unreviewed critical dependency, unresolved host patching, startup bypasses migrations/health, prohibited configuration starts, topology differs, hosted Supabase/R2/Supabase Storage appears, or recovery depends on undocumented manual state.
- **Rollback or recovery boundary:** Stop the new environment, retain the last approved environment unchanged, restore only from verified backups, and require architecture/security review before another attempt.
- **Blocks:** Both.

### `RF-15` — Database migration, backup, rollback, restore, and revision `0008` boundaries

- **Objective:** Prove the accepted migration chain can be assessed and applied safely to the approved target with retained data, explicit stop handling, recoverable backups, and no rewriting of issued history.
- **Owner:** Unassigned. `OD-01` must name a database operator, application owner, data/privacy reviewer, migration reviewer, and rollback/restore approver.
- **Prerequisite owner decisions:** `OD-01`, `OD-09`, `OD-10`, `OD-11`, `OD-13`, `OD-14`, `OD-15`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-15-database-migration.md` with issued-revision hashes, one-head/current-revision evidence, preflight query results, sanitized retained-data inventory, backup/restore proof, isolated upgrade/check/downgrade/re-upgrade results where representable, timing/capacity observations, and approved stop/reconciliation records.
- **Execution procedure or future runbook:** Freeze schema writes under approved authority; verify source and image revision; take and validate coordinated backups; restore a copy into isolation; preflight duplicate non-null legacy provider envelope IDs and rejected-envelope downgrade constraints before DDL; inspect historical profile/audit evidence used for slug locks; upgrade to `20260719_0008`; verify one head and model/schema agreement; validate representative evidence; exercise rollback only when representable; document forward-fix or restore strategy; never rewrite issued migration files.
- **Pass/fail criterion:** Pass when preflight is unambiguous, backup restore is proven, upgrade reaches exactly `20260719_0008`, schema/model checks are clean, historical evidence remains accurate, slug locks derive from authoritative evidence, recovery objectives are met, and the approved recovery method succeeds in isolation.
- **Stop condition:** Duplicate legacy provider envelope IDs, unreviewable profile/audit provenance, rejected-envelope evidence during downgrade, unknown/extra head, model drift, backup/restore failure, unapproved retained data, unexpected DDL/data loss, or need to relabel/deduplicate evidence.
- **Rollback or recovery boundary:** Migration `0008` may deliberately refuse downgrade. Do not force it. Use the owner-approved forward-fix or restore-from-verified-backup boundary, preserve rejected/predecessor evidence, and resume only after data/privacy/migration approval.
- **Blocks:** Both.

### `RF-16` — Genuine authenticated administrator/operator browser ceremonies

- **Objective:** Prove the accepted workflows against the approved integrated stack with genuine authentication, server-side authorization, PostgreSQL, MinIO/ClamAV where relevant, and real approved Documenso connectivity, without final activation or role grant.
- **Owner:** Unassigned. `OD-01` must name the ceremony operator, security observer, onboarding process owner, Documenso operator, profile/content approver, and evidence reviewer.
- **Prerequisite owner decisions:** `OD-01`, `OD-02`, `OD-03`, `OD-05`, `OD-07`, `OD-08`, `OD-15`, `OD-18`, `OD-19`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-16-authenticated-browser-ceremonies.md` with scenario IDs, sanitized preconditions/record identifiers, screen/log evidence free of secrets/PII, audit-event references, expected/actual outcomes, cleanup record, and independent review.
- **Execution procedure or future runbook:** Use only approved disposable synthetic identities until `OD-03` permits otherwise. Complete these separate ceremonies:
  1. Link only the seeded placeholder administrator through the local-only command, complete genuine TOTP/AAL2, and prove `/admin`, candidate review, and onboarding APIs authorize server-side; AAL1 and wrong-role identities remain denied.
  2. Prepare one candidate with at least two distinguishable application attempts and an unused plan; edit/reorder the unused plan; assign the selected exact conditionally-selected application; prove the other attempt is unchanged; prove later plan content/availability edits fail permanently; do not activate.
  3. Satisfy one of the three manual gates with bounded evidence, correct/reopen it with a reason, and verify append-oriented exact-assignment history. Prove the two derived gates expose no manual satisfy/reopen path and that superseded-assignment evidence does not affect current readiness.
  4. Link and refresh an envelope against the approved exact HTTPS Documenso origin; prove provider/network/`DRAFT` ambiguity leaves readiness unsatisfied; prove provider-confirmed completion satisfies only the exact assignment; reject and replace an envelope while preserving the non-satisfying predecessor; prove redirect refusal.
  5. Create a profile only from a server-projected eligible active agent relationship already authorized by fixtures/approved data; approve and publish with an available slug; unpublish/suspend as permitted; prove the first slug remains reserved and immutable; prove `/admin/content` remains absent. Do not create or grant an agent role.
- **Pass/fail criterion:** Pass only when every ceremony uses genuine Auth/session/API/database/provider boundaries, expected denial paths fail safely, audit/provenance is exact, no cross-application/assignment leakage occurs, no secret/PII enters evidence, and no final activation, candidate-to-agent transition, or role grant occurs.
- **Stop condition:** Mocked provider or authentication substituted for required genuine evidence, wrong application/assignment changes, plan remains editable after use, derived gate can be changed manually, ambiguous provider state satisfies readiness, predecessor history changes/disappears, ineligible profile publishes, slug releases, `/admin/content` reappears, token/PII exposure, or any activation/role grant.
- **Rollback or recovery boundary:** Stop the ceremony, preserve audit/evidence, revoke disposable sessions, leave immutable history intact, use only supported corrective operations, clean synthetic records under an approved cleanup procedure, and investigate before rerun. Never edit tables directly to make a ceremony pass.
- **Blocks:** Controlled pilot and production.

### `RF-17` — Privacy, legal, regulatory, claims, content, and accessibility review

- **Objective:** Obtain explicit specialist approval or documented blocking findings for all public, candidate, onboarding, document, consent, complaint, profile, and operating practices.
- **Owner:** Unassigned. `OD-01`, `OD-15`, and `OD-16` must name the approvers; engineering cannot fill these roles by inference.
- **Prerequisite owner decisions:** `OD-01`, `OD-03`, `OD-10`, `OD-11`, `OD-15`, `OD-16`, `OD-18`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-17-specialist-reviews.md` linking separate signed/dated privacy, legal, Ontario regulatory/advertising, claims/content/licensing, complaints/consent, and accessibility findings with scope, version, exceptions, remediation, and expiry/re-review triggers.
- **Execution procedure or future runbook:** Provide reviewers the exact deployed content/configuration, data inventory/flows, disclosure and consent versions, retention/hold plan, Documenso role, FSRA administrative-verification wording, profile/public claims, complaint/accessibility pages, and browser evidence. Accessibility review must include approved automated coverage and manual keyboard, focus, zoom/reflow, screen-reader, contrast, reduced-motion, touch-target, responsive, and document-alternative checks.
- **Pass/fail criterion:** Pass only when every required reviewer issues explicit approval for the exact scope/version or all blocking findings are remediated and re-approved; claims and licensing are evidenced; no automated regulatory/legal/e-sign compliance claim is made; accessibility exceptions have named authority, impact, compensating measure, and deadline.
- **Stop condition:** Missing reviewer/approval, unresolved high-impact finding, unlicensed asset, unapproved legal/regulatory text or public claim, inaccessible critical journey, retention/data use conflict, or attempt to treat engineering tests as certification.
- **Rollback or recovery boundary:** Keep affected content/route/workflow non-public or pilot-disabled, restore the last approved content/configuration under change control, and obtain re-review. Do not invent substitute wording or legal conclusions.
- **Blocks:** Both.

### `RF-18` — Pilot roster, eligibility, support, go/no-go, and evidence package

- **Objective:** Bound the pilot to approved people, data, actions, support, timing, and stop criteria and produce one reviewable go/no-go package.
- **Owner:** Unassigned. `OD-01`, `OD-02`, and `OD-17` must name the pilot owner, roster custodian, support lead, incident contact, evidence reviewer, and go/no-go decision maker.
- **Prerequisite owner decisions:** All pilot-blocking decisions in Section 6, especially `OD-01`, `OD-02`, `OD-03`, `OD-13`, `OD-15`, `OD-17`, `OD-18`, and `OD-19`.
- **Evidence artifact:** `docs/evidence/phase-1f/RF-18-pilot-go-no-go-package.md` containing the approved pilot charter, roster/eligibility record in a restricted location, training/support acknowledgment, risk register, all pilot-blocking RF results, unresolved nonblocking production deferrals, stop/rollback contacts, and signed go/no-go decision.
- **Execution procedure or future runbook:** Verify each participant's eligibility and access; issue least privilege; train administrators/support on exact-application selection, evidence handling, Documenso ambiguity, privacy, incident stop, and no-activation boundary; run pre-pilot health/backup/restore/alert/browser checks; hold go/no-go review; monitor daily/approved cadence; review access and incidents; execute end-of-pilot revocation, export/retention/deletion/hold, and evidence closure.
- **Pass/fail criterion:** Go only when all controlled-pilot blockers are passed, every material owner decision and specialist review is approved, roster/support/escalation are active, backup/restore and stop procedures are proven, browser ceremonies pass, no critical/high unresolved risk remains, and the named owner signs the exact evidence package. Production requires a separate decision and all production blockers passed.
- **Stop condition:** Unapproved participant/data, missing support/on-call coverage, failed blocker, stale evidence, unresolved material legal/privacy/security/accessibility risk, inability to restore/stop, role/access drift, unsafe provider/scanner state, or request to activate/grant roles.
- **Rollback or recovery boundary:** Do not start or immediately stop the pilot under the approved incident/stop procedure; revoke pilot access/sessions, preserve evidence, apply approved data-lifecycle actions, restore only from verified backups if necessary, and require a new go/no-go package before restart.
- **Blocks:** Controlled pilot; the completed pilot report and separately defined production criteria also inform production approval but do not automatically grant it.

## 8. Privacy, legal, regulatory, claims, and accessibility review register

The following reviews are separate gates; one reviewer or approval must not be assumed to cover another discipline unless `OD-01` and `OD-15` explicitly approve that accountability.

| Review                         | Required scope                                                                                                                                                                                             | Minimum artifact                                                                         | Current state            |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------ |
| Privacy                        | Data inventory/flows, purpose/minimization, consent/disclosure, processors, access, retention, correction/export/deletion, legal hold, logs, backups, pilot closure, incident handling.                    | Signed/dated review with scope/version, findings, required changes, and approval/denial. | Blocked — owner decision |
| Legal                          | Terms/notices, e-sign process role, complaints, consent, retention/hold, incident communications, pilot participant terms, and data-processing responsibilities.                                           | Signed/dated legal review; no engineering paraphrase as conclusion.                      | Blocked — owner decision |
| Ontario regulatory/advertising | Brokerage/agent identity, FSRA-related wording, titles, profile publication, recruitment claims, public claims, and prohibited automation representations.                                                 | Signed/dated regulatory/advertising review.                                              | Blocked — owner decision |
| Claims/content/licensing       | Public facts, principal-broker identity/title, testimonials/metrics/ratings/lender or approval claims, logo/font/image licences, and agent content.                                                        | Approved content inventory and licence evidence.                                         | Blocked — owner decision |
| Accessibility                  | Public, candidate, administrator, Auth/MFA, document, onboarding, e-sign-link, errors, responsive views, keyboard, screen reader, contrast, zoom/reflow, motion, touch targets, and document alternatives. | Automated report plus manual reviewer record, defects, exceptions, and approval.         | Blocked — owner decision |

## 9. Controlled-pilot go/no-go criteria

### 9.1 Mandatory go criteria

A controlled pilot may be recommended only when:

1. The owner has approved this plan and all pilot-blocking decisions in Section 6.
2. Named accountable owners, reviewers, support contacts, incident contacts, and go/no-go authority are recorded.
3. Every work package marked as a controlled-pilot blocker is `Passed for controlled pilot` or `Not applicable by approved scope` with a non-weakened rationale.
4. Privacy, legal, regulatory/claims/content/licensing, and accessibility reviews approve the exact pilot scope or all blocking findings are remediated and re-approved.
5. The pilot charter, roster, eligibility, permitted data, support hours, success measures, duration, stop triggers, and end-of-pilot procedure are approved.
6. The intended host/topology passes firewall, listener, ingress, TLS, secrets, access, Auth/email, logging, monitoring, alert, backup, isolated restore, incident, and migration evidence.
7. Supabase Studio is local-only, Supabase Storage/S3 remain disabled, MinIO remains private and recoverable, and ClamAV is current, monitored, alerted, and fail closed.
8. The approved Documenso deployment passes exact-version/API/HTTPS/redirect/failure/replacement/backup/monitoring evidence.
9. Genuine authenticated administrator/operator browser ceremonies in `RF-16` pass without final activation or role grant.
10. The evidence package identifies the exact branch/revision/environment, contains no secrets or unnecessary PII, and is independently reviewed.
11. No critical/high unresolved security, privacy, legal, regulatory, claims, accessibility, data-integrity, backup/restore, or incident-response risk remains.
12. The named owner records an explicit go decision. Source acceptance, passing tests, or a successful ceremony alone is insufficient.

### 9.2 Mandatory no-go or immediate-stop criteria

A no-go or stop is mandatory for any of the following:

- unresolved material owner decision or missing named accountable owner;
- unapproved real personal data or prohibited borrower data;
- public/unapproved exposure of Studio, PostgreSQL, MinIO, clamd, Supabase internals, Documenso administration, or privileged APIs;
- Supabase Storage/S3 enabled or application object storage moved away from MinIO;
- stale/unhealthy/unmonitored ClamAV or any scanner bypass/false success;
- failed backup, isolated restore, migration preflight, migration integrity, or return-to-service exercise;
- duplicate legacy provider envelope IDs before `0008` upgrade DDL, or a proposed forced downgrade with rejected-envelope evidence;
- identity-only access, missing administrator AAL2, failed revocation/offboarding, unknown privileged credential, or secret leakage;
- Documenso HTTP/redirect acceptance, version/API mismatch, provider ambiguity satisfying readiness, lost predecessor history, or unapproved webhook assumptions;
- token, cookie, private URL, document content, raw sensitive payload, or unnecessary PII in logs/evidence;
- unresolved specialist-review blocker or inaccessible critical journey;
- unavailable support/escalation/incident authority;
- wrong-application or cross-assignment mutation;
- final activation, candidate-to-agent transition, or agent-role grant request or occurrence;
- evidence produced from an unapproved worktree/environment or lacking exact provenance.

## 10. Production approval and deferred production work

Controlled-pilot approval does not grant production approval. Production requires a separate owner decision and fresh evidence at the production scope, topology, data volume, roster, support model, and time of release.

The following remain deferred or separately gated and must not be smuggled into Phase 1F readiness execution:

- final candidate activation, candidate-to-agent transition, and agent-role grant;
- borrower application, borrower identity/financial/document data, underwriting, lender submission, commissions, and payroll;
- a full CRM, lead assignment workflow, bulk export, marketing automation, or independent agent portals/microsites;
- custom e-signature functionality or claims that the application itself establishes signature legality;
- automated FSRA/FINTRAC or other regulatory-verification claims;
- Documenso webhooks unless a separate approved decision/specification defines the exact deployed-version behavior and security model;
- multi-region architecture, high availability, or disaster-recovery topology not approved in the owner-decision register;
- new cloud vendors, hosted Supabase, Cloudflare R2, Supabase Storage, new sensitive-data classes, or new external integrations;
- customer-facing data-rights automation, immutable audit export/tamper-evidence system, or other production enhancements not separately approved.

Deprecation remediation for Starlette `TestClient` and Alembic configuration should be tracked as bounded maintenance. It is not an accepted-suite failure, and it does not supersede the operational blockers above.

## 11. Planning sequence and approval gates

This sequence is a planning dependency order, not execution authorization:

1. Resolve `OD-01` through `OD-19` or explicitly record approved exclusions. Final activation and agent-role grant remain excluded rather than open for Phase 1F decision.
2. Approve the pilot charter/data boundary and the exact production/pilot topology.
3. Approve specialist review scope and assign reviewers.
4. Approve evidence handling, secrets, backup objectives, retention, incident, monitoring, and support policies.
5. Approve Auth/email and Documenso vendor/version/configuration decisions.
6. Convert each `RF` item into a separately reviewed runbook/change with environment, commands, rollback, and evidence handling appropriate to the approved topology.
7. Obtain separate authorization for non-destructive isolated evidence execution.
8. Obtain separate authorization for any credential, firewall, vendor, deployment, shared-database, backup/restore, or destructive action.
9. Execute and review evidence; failed or blocked items return to planning/change control.
10. Assemble the controlled-pilot package and obtain an explicit go/no-go decision.
11. After a bounded pilot and closure review, define and obtain a separate production go/no-go decision. Do not infer production approval from pilot success.

## 12. Plan acceptance criteria

This draft is ready for owner review when:

- all six required categories are distinct: accepted implementation, required operational evidence, owner decisions, specialist reviews, pilot go/no-go criteria, and deferred production work;
- every required readiness topic has an objective, unassigned/named owner state, prerequisite decision, evidence artifact, future procedure, pass/fail criterion, stop condition, recovery boundary, and pilot/production blocker classification;
- no legal conclusion, retention period, vendor, credential, network topology, webhook behavior, data-use permission, or named owner is invented;
- exact-application, exact-assignment, fail-closed, private-storage, MFA, lifecycle, and no-activation boundaries are preserved;
- migration `20260719_0008` stop behavior is explicit and cannot be interpreted as permission to force or rewrite evidence;
- the complete API suite is described only by its recorded successful exit status, without a manufactured exact count;
- the document contains no runtime implementation, migration, infrastructure change, secret, deployment command execution, or publication action.

Approval of this plan is itself an owner decision. It does not authorize the planned work to execute; each operational or repository-changing action still requires its applicable separate authorization.
