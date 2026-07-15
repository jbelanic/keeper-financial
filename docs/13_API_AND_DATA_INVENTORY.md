# Initial API and Data Inventory

## API routes

| Method | Route | Access | Purpose |
|---|---|---|---|
| GET | `/health` | Public | Process health; no dependency detail or secret. |
| GET | `/health/db` | Public | Distinguishes reachable/unreachable application database. |
| GET | `/api/v1/auth/access?area=candidate|admin` | Authenticated | Maps verified Supabase identity to local authorization. |
| POST | `/api/v1/leads` | Public | Minimal contact-first inquiry and separate consent evidence. |
| GET | `/api/v1/leads?limit=&offset=&status=` | Brokerage admin | No-store, bounded newest-first lead queue; optional lifecycle status only. |
| POST | `/api/v1/leads/{id}/marketing-consent/withdrawal` | Brokerage admin | Idempotently withdraws only existing marketing consent; no-store. |
| GET | `/api/v1/integrations/mortgage-application` | Public | Validated redirect to configured external provider; `503` when disabled/unsafe. |
| POST | `/api/v1/candidates/{id}/status` | Brokerage admin | Service-enforced lifecycle transition and audit event. |
| POST | `/api/v1/agents/{id}/status` | Brokerage admin | Service-enforced approval/publication lifecycle. |
| GET | `/api/v1/documents/{id}/download` | Owning candidate or brokerage admin | Authorized, audited local response or short-lived R2 redirect; quarantine denied. |

Production disables OpenAPI. Local and controlled non-production expose `/openapi.json` and `/docs`.

## Database models

| Model | Foundation responsibility |
|---|---|
| `User`, `UserIdentity` | Local account and verified Supabase subject link. |
| `Role`, `UserRole` | Application authorization grants. |
| `Candidate`, `CandidateApplication`, `CandidateStatusHistory` | Recruitment relationship, controlled application revision state, append-oriented lifecycle evidence. |
| `RecruitmentPosting` | Draft/published/closed/archived opportunity. |
| `OnboardingPlan`, `OnboardingTask`, `CandidateOnboardingTask` | Reusable plan and assigned task state. |
| `ControlledDocument`, `DocumentVersion` | Logical controlled document and immutable issued-file metadata. |
| `CandidateDocument` | Private object metadata, hash, quarantine and status—not object bytes. |
| `PolicyAcknowledgement` | Exact document-version and wording evidence. |
| `AgentProfile` | Approval-controlled public profile metadata and publication state. |
| `LeadInquiry` | Approved minimal contact fields only; server-owned source/status. Queue indexes support `(created_at,id)` and `(status,created_at,id)`. |
| `ConsentRecord` | Server-versioned service or optional marketing evidence, grant time, optional withdrawal time, and trusted capture source. |
| `AuditEvent` | Append-oriented safe lead creation, marketing grant/withdrawal, lifecycle, publication, and document event metadata. |

UUIDs are primary keys. PostgreSQL check constraints reinforce service statuses. Service code—not client input or database constraints alone—owns valid transitions. There is deliberately no mortgage deal, borrower finance, borrower document, credit, lender submission, commission, or payroll model.

## Contract generation

FastAPI/Pydantic owns the OpenAPI contract. `make openapi` exports it and runs `openapi-typescript` to create TypeScript declarations. Generated output should change in the same review as API schema changes.

`packages/contracts/src/index.ts` exports generated `paths`, `operations`, and `components` while retaining the hand-authored `PortalArea`. The public lead operation has no bearer security requirement; list and withdrawal declare HTTP bearer security; redirect remains public and documents its `307`, validation, and fail-closed `503` responses.
