# API and Data Inventory

## API routes

### Foundation through Phase 1C

| Method     | Route                                                                     | Access                              | Purpose                                                                      |
| ---------- | ------------------------------------------------------------------------- | ----------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| GET        | `/health`                                                                 | Public                              | Process health without dependency detail or secrets.                         |
| GET        | `/health/db`                                                              | Public                              | Application-database reachability.                                           |
| GET        | `/api/v1/auth/access?area={candidate                                      | admin}`                             | Authenticated                                                                | Maps verified Supabase identity to local role, relationship, lifecycle, and MFA authorization. |
| POST       | `/api/v1/leads`                                                           | Public                              | Minimal contact-first inquiry and separate consent evidence.                 |
| GET        | `/api/v1/leads?limit=&offset=&status=`                                    | Brokerage admin                     | No-store bounded lead queue.                                                 |
| POST       | `/api/v1/leads/{lead_id}/marketing-consent/withdrawal`                    | Brokerage admin                     | Idempotent marketing-only withdrawal.                                        |
| GET        | `/api/v1/integrations/mortgage-application`                               | Public                              | Validated configured external-provider redirect.                             |
| GET        | `/api/v1/recruitment/postings`                                            | Public                              | Published recruitment summaries only.                                        |
| GET        | `/api/v1/recruitment/postings/{slug}`                                     | Public                              | Published posting detail; non-public records return safe `404`.              |
| POST       | `/api/v1/recruitment/postings/{slug}/applications/start`                  | Verified external identity          | Atomic, narrow candidate provisioning and posting-specific attempt creation. |
| GET, POST  | `/api/v1/admin/recruitment-postings`                                      | Brokerage admin                     | No-store list and bounded draft creation.                                    |
| PATCH      | `/api/v1/admin/recruitment-postings/{posting_id}`                         | Brokerage admin                     | Versioned bounded edit.                                                      |
| POST       | `/api/v1/admin/recruitment-postings/{posting_id}/{action}`                | Brokerage admin                     | Explicit `publish`, `close`, or `archive` transition with audit evidence.    |
| GET        | `/api/v1/candidate/privacy-disclosure`                                    | Candidate                           | Server-owned disclosure text/version.                                        |
| GET        | `/api/v1/candidate/applications`                                          | Candidate                           | Owned posting-specific applications.                                         |
| GET        | `/api/v1/candidate/applications/status`                                   | Candidate                           | Minimal allow-listed application status.                                     |
| GET, PATCH | `/api/v1/candidate/applications/{application_id}`                         | Owning candidate                    | Owned read and revision-checked draft update.                                |
| POST       | `/api/v1/candidate/applications/{application_id}/submit`                  | Owning candidate                    | Exactly-once submission/privacy/history/audit transaction.                   |
| POST       | `/api/v1/candidate/applications/{application_id}/withdraw`                | Owning candidate                    | Application-specific audited withdrawal.                                     |
| GET, POST  | `/api/v1/candidate/applications/{application_id}/documents`               | Owning candidate at AAL2            | Private metadata list and validated clean-before-persistence upload.         |
| DELETE     | `/api/v1/candidate/applications/{application_id}/documents/{document_id}` | Owning candidate at AAL2            | Draft-only document removal.                                                 |
| GET        | `/api/v1/documents/{document_id}/download`                                | Owning candidate or brokerage admin | Authorized/audited local response or short-lived private MinIO redirect.     |
| POST       | `/api/v1/upload-document`                                                 | Active candidate at AAL2            | Non-persisting PDF/JPEG/PNG validation and ClamAV scan, up to exactly 5 MiB. |

### Phase 1D review and onboarding

| Method    | Route                                                                              | Access           | Purpose                                                                                                           |
| --------- | ---------------------------------------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| GET       | `/api/v1/admin/candidates`                                                         | Brokerage admin  | No-store bounded review queue.                                                                                    |
| GET       | `/api/v1/admin/candidates/{candidate_id}`                                          | Brokerage admin  | Review detail for an eligible candidate.                                                                          |
| POST      | `/api/v1/admin/candidates/{candidate_id}/interview`                                | Brokerage admin  | Record interview state and bounded internal notes.                                                                |
| POST      | `/api/v1/admin/candidates/{candidate_id}/information-requests`                     | Brokerage admin  | Create a bounded information request and lifecycle/audit evidence.                                                |
| POST      | `/api/v1/admin/candidates/{candidate_id}/decision`                                 | Brokerage admin  | Apply an allowed administrative decision transition with required reason policy.                                  |
| POST      | `/api/v1/admin/candidates/{candidate_id}/assign-onboarding?plan_id={plan_id}`      | Brokerage admin  | Assign an eligible candidate to an existing onboarding plan.                                                      |
| GET, POST | `/api/v1/admin/onboarding/plans`                                                   | Brokerage admin  | List or create reusable plans with bounded task templates.                                                        |
| GET       | `/api/v1/admin/onboarding/plans/{plan_id}`                                         | Brokerage admin  | Retrieve one plan and its ordered tasks.                                                                          |
| POST      | `/api/v1/admin/onboarding/candidates/{candidate_id}/tasks/{task_id}/review`        | Brokerage admin  | Accept/reject submitted candidate task evidence.                                                                  |
| POST      | `/api/v1/admin/onboarding/candidates/{candidate_id}/esign-envelopes`               | Brokerage admin  | Link an external e-signature envelope without custom signing.                                                     |
| PATCH     | `/api/v1/admin/onboarding/candidates/{candidate_id}/esign-envelopes/{envelope_id}` | Brokerage admin  | Update external envelope reference/status.                                                                        |
| POST      | `/api/v1/admin/onboarding/candidates/{candidate_id}/gates`                         | Brokerage admin  | Satisfy an allow-listed activation gate.                                                                          |
| GET       | `/api/v1/admin/onboarding/documents`                                               | Brokerage admin  | List controlled documents and current issued versions.                                                            |
| GET       | `/api/v1/candidate/onboarding`                                                     | Candidate        | Owned assignment, task, gate, document, acknowledgement, and envelope dashboard.                                  |
| POST      | `/api/v1/candidate/onboarding/tasks/{task_id}/evidence`                            | Owning candidate | Submit bounded task evidence.                                                                                     |
| POST      | `/api/v1/candidate/onboarding/acknowledgements`                                    | Owning candidate | Record acknowledgement of an exact document version; the assignment-authorization limitation is documented below. |

### Phase 1E agent profiles

| Method     | Route                                       | Access          | Purpose                                                                              |
| ---------- | ------------------------------------------- | --------------- | ------------------------------------------------------------------------------------ |
| GET        | `/api/v1/agents`                            | Public          | Published-only safe summaries for eligible active agents.                            |
| GET        | `/api/v1/agents/{slug}`                     | Public          | Published-only safe detail; non-public/ineligible records return `404`.              |
| GET, POST  | `/api/v1/admin/agent-profiles`              | Brokerage admin | List eligible profiles or create a bounded draft for an active agent relationship.   |
| GET, PATCH | `/api/v1/admin/agent-profiles/{profile_id}` | Brokerage admin | Retrieve/update a profile; editing published content returns it to pending approval. |
| POST       | `/api/v1/agents/{profile_id}/status`        | Brokerage admin | Apply the approval/publication/suspension/archive lifecycle with audit evidence.     |

Production disables OpenAPI. Local and controlled non-production expose `/openapi.json` and `/docs`.

## Browser authentication and candidate provisioning orchestration

The browser routes orchestrate the existing API inventory; they are not additional FastAPI routes:

1. A published `/careers/{slug}` page currently links only to `/auth/register?posting={slug}`.
2. Registration supplies `/auth/callback?posting={slug}` as the Supabase email-confirmation redirect.
3. `/auth/callback` exchanges the authorization code for a Supabase SSR cookie session and calls `POST /api/v1/recruitment/postings/{slug}/applications/start` with the resulting access token.
4. The application-start route is the only approved narrow local-provisioning boundary. It validates the verified external identity and published posting before creating or reusing the local user, identity, candidate role/relationship, and posting-specific application attempt.
5. Generic `/auth/sign-in` performs password authentication and returns to an allow-listed portal root. It intentionally does not call application start, infer a posting, or provision local access.
6. Candidate/admin server components read the Supabase SSR cookie session and then call `/api/v1/auth/access?area={candidate|admin}`; the application database remains the authorization authority.

Current limitation at the Phase 1F readiness gate: the public posting has no posting-preserving existing-user sign-in action, and generic sign-in drops posting context. Consequently, a confirmed but locally unmapped existing user can authenticate but is correctly denied candidate access and cannot reach the only supported posting-bound provisioning operation. Callback/session persistence exists in code, but real local callback, refresh, expiry/revocation, and cross-request cookie behavior have not been adequately verified. These are unresolved Phase 1C completion defects; this inventory does not claim remediation.

## Implemented Phase 1D and Phase 1E data flows

- Review: local authorized admin → review queue/detail → interview, information request, or decision service → PostgreSQL lifecycle/history/audit transaction.
- Onboarding: authorized admin → reusable plan/assignment → candidate-owned dashboard and evidence/acknowledgement → admin task review and allow-listed gates → PostgreSQL records and audit evidence.
- Controlled documents: PostgreSQL document/version metadata → candidate onboarding projection → exact-version acknowledgement; any private bytes continue through the authorized MinIO download boundary. The current acknowledgement operation does not yet prove that the submitted version was assigned to that candidate.
- External e-signature: admin stores only bounded envelope references/status through the adapter boundary; the application does not sign documents.
- Agent publication: authorized admin → eligible active local agent relationship → draft/update → approval/publication transition → safe public list/detail projection. Suspension/archive removes the public projection.
- File acceptance: authenticated AAL2 request → bounded read and type/structure checks → fail-closed ClamAV scan → private MinIO persistence only on clean → PostgreSQL metadata/audit commit. Rejected or unavailable-scan bytes are not persisted.

## Live data services

The authoritative live environment is the local Linux Docker Compose stack. Application/authorization data uses durable `db` PostgreSQL, private object bytes use durable `minio`, and malware decisions use healthchecked local `clamav` with persistent signatures. Metadata remains in PostgreSQL. The local Supabase CLI stack supplies identity only and has its own separate internal database. No hosted Supabase or Cloudflare R2 inventory exists.

## Database models

| Model                                                         | Foundation responsibility                                                                                                                                                                                                                              |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `User`, `UserIdentity`                                        | Local account and verified Supabase subject link.                                                                                                                                                                                                      |
| `Role`, `UserRole`                                            | Application authorization grants.                                                                                                                                                                                                                      |
| `Candidate`, `CandidateApplication`, `CandidateStatusHistory` | Recruitment relationship, required posting-specific application/attempt, controlled revision and application-level state, append-oriented lifecycle evidence. Supports concurrent applications but only one nonterminal attempt per candidate/posting. |
| `RecruitmentPosting`                                          | Draft/published/closed/archived opportunity.                                                                                                                                                                                                           |
| `OnboardingPlan`, `OnboardingTask`, `CandidateOnboardingTask` | Reusable plan and assigned task state.                                                                                                                                                                                                                 |
| `ControlledDocument`, `DocumentVersion`                       | Logical controlled document and immutable issued-file metadata.                                                                                                                                                                                        |
| `CandidateEmploymentEntry`, `CandidateEducationEntry`         | Bounded normalized repeat groups for the approved questionnaire; no unrestricted answer JSON.                                                                                                                                                          |
| `CandidateDocument`                                           | Required candidate/application/category linkage plus private random object key, declared/detected MIME, hash, size, current/quarantine/scan status, and timestamps—not object bytes.                                                                   |
| `PolicyAcknowledgement`                                       | Exact document-version and wording evidence.                                                                                                                                                                                                           |
| `AgentProfile`                                                | Approval-controlled public profile content, licence/contact/image/social metadata, safe language/service/specialty lists, version, and publication evidence. It contains no borrower or underwriting data.                                             |
| `LeadInquiry`                                                 | Approved minimal contact fields only; server-owned source/status. Queue indexes support `(created_at,id)` and `(status,created_at,id)`.                                                                                                                |
| `ConsentRecord`                                               | Server-versioned service or optional marketing evidence, grant time, optional withdrawal time, and trusted capture source.                                                                                                                             |
| `AuditEvent`                                                  | Append-oriented safe lead creation, marketing grant/withdrawal, lifecycle, publication, and document event metadata.                                                                                                                                   |

UUIDs are primary keys. PostgreSQL check constraints reinforce service statuses. Service code—not client input or database constraints alone—owns valid transitions. There is deliberately no mortgage deal, borrower finance, borrower document, credit, lender submission, commission, or payroll model.

Migration `20260715_0003` brings the schema into conformance with `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`: posting and immutable source provenance are mandatory, attempt/application lifecycle is distinct, the questionnaire/disclosure are version-controlled, and every new candidate document has explicit application/category linkage. The migration refuses to invent provenance or linkage for incompatible legacy rows.

Migration `20260717_0005` creates the previously missing `agent_profiles` table, chained from `20260716_0004`. Its columns, status check, user foreign keys, unique user/slug boundaries, and publication index match the SQLAlchemy model.

## Contract generation

FastAPI/Pydantic owns the OpenAPI contract. `make openapi` exports it and runs `openapi-typescript` to create TypeScript declarations. Generated output should change in the same review as API schema changes.

`packages/contracts/src/index.ts` exports generated `paths`, `operations`, and `components` while retaining the hand-authored `PortalArea`. Public posting and published-agent operations have no bearer declaration; provisioning, candidate, document, and administration operations declare HTTP bearer security. Candidate and public-agent response schemas structurally omit internal reason/note/actor/audit/decision and unpublished lifecycle fields.
