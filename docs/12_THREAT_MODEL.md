# Phase 1B Threat Model Summary

This is an engineering threat model, not a legal or compliance certification.

## Assets and trust boundaries

- Public content crosses an untrusted browser/server boundary.
- Supabase establishes external identity; the FastAPI/database boundary grants application authorization.
- Candidate and onboarding data is personal; candidate files and executed agreements are restricted.
- PostgreSQL holds roles, lifecycle, consent, and audit evidence.
- Local filesystem is trusted only in local development. Private R2 is the nonlocal object boundary.
- Mortgage application, CRM, e-signature, email, and future malware scanning are external-provider boundaries.

## Primary threats and controls

| Threat | Phase 0 control | Remaining work |
|---|---|---|
| Valid token used as automatic portal access | JWT verification plus verified local identity, active user, role, relationship, lifecycle, and MFA policy | Session revocation integration and operational access review. |
| Candidate accesses another candidate’s file | Opaque UUID route, random object key, server ownership/role check on every retrieval, audit event | Upload workflow authorization and adversarial integration tests against R2. |
| Public/private object exposure | No public object route or URL, local-only filesystem guard, private R2 adapter, short signed retrieval | Bucket-policy review and production probe. |
| Unsafe file | MIME/size allow-list, random key, quarantine state blocks retrieval | Magic-byte/extension checks and selected malware scanner. |
| Open redirect or sensitive redirect query | Configuration-only destination, HTTPS and exact-host allow-list, query/fragment/credential rejection, safe slug grammar, and approved agent mapping | Vendor URL/map approval and controlled operational update process. |
| Contact form becomes a mortgage application or abuse target | Explicit field allow-list, extra/control/sensitive-field rejection, length limits, prominent/adjacent UI warnings, zero-length automation trap, and bounded direct-peer rate limiter that fails closed | Legal/privacy approval of draft wording; deployment-level aggregate limiting, trusted-proxy design, monitoring, and tuning before production. |
| Caller rewrites consent evidence | Immutable server registry owns exact draft engineering wording versions, privacy version, source, and capture source; override fields are forbidden | Final legal/privacy wording and immutable version approval. |
| Consent bundled with service or withdrawal damages service evidence | Required service acknowledgement, separately optional marketing record, row-locked/idempotent admin withdrawal, and safe first-withdrawal audit | Customer-facing withdrawal channel/process, retention/deletion policy, and concurrency integration test on PostgreSQL. |
| Lead/contact data leaks through admin URLs or caches | Server-protected layout, FastAPI `require_admin`, nonlocal AAL2, no-store API/server fetch, safe page/status URL filters only, bounded response | Browser/proxy cache probes and production access review. |
| Unauthorized lifecycle/publication change | Backend transition maps, reason requirements, admin role, approval evidence, audit event | Activation-gate implementation and principal-broker approval policy. |
| Tokens or personal payloads leak through logs/audits | Structured request logs contain method/path/status/IDs only; lead/consent audits contain identifiers, status/source/capture source only | Central log pipeline tests and redaction review. |
| Unsafe deployment configuration | Pydantic startup validation rejects local storage, dev auth, debug, wildcard/loopback/non-HTTPS origins, missing R2, and missing admin MFA outside local | Deployment-policy test in selected hosting platform. |
| Audit evidence altered | No general update/delete API; append-oriented service | Database privileges, retention, immutable export/storage decision. |

## Abuse cases explicitly excluded

The platform has no borrower application, mortgage underwriting, credit, lender-submission, commission, payroll, or custom signing model. Adding those fields or flows requires scope and threat-model change control.
