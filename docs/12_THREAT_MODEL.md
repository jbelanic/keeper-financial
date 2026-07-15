# Phase 1C Threat Model Summary

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
| Candidate accesses another application or file | Posting-specific local relationship, opaque UUID, ownership check on read/save/submit/withdraw/upload/list/download, random object key, application linkage, AAL2 for restricted documents, safe `404` cross-owner behavior, audit event | Hosted identity/R2 adversarial integration and production access review. |
| Public/private object exposure | No public object route or URL, local-only filesystem guard, private R2 adapter, short signed retrieval | Bucket-policy review and production probe. |
| Unsafe file | Exact category/extension/declared-MIME/signature agreement, streaming size limit, sanitized filename metadata, random key, pending quarantine, scanner adapter, non-clean download denial, orphan cleanup, safe rejection/scan audits | Select and validate a production malware-scanning provider; until then nonlocal upload fails closed. |
| Verified token self-provisions privileged access | Dedicated published-posting start boundary validates signed verified subject/email, rejects link conflicts, grants only candidate role, creates only candidate/application relationships, and remains atomic/idempotent | Hosted Supabase end-to-end and account-recovery/session-revocation tests. |
| Candidate changes posting, privacy evidence, lifecycle, or submitted answers | Extra-forbid typed schemas, server-owned source snapshot/schema/disclosure/revision/state/timestamps, row locks and revision checks, immutable submitted questionnaire | Operational review of retention/deletion and future controlled reopen design in Phase 1D. |
| Draft/closed/archived posting becomes public | Explicit lifecycle map, published-only indexed queries, direct-slug indistinguishable `404`, plain-text bounded fields, admin role/AAL2, publication actor/time/audit | Production cache/proxy probes and operational approval process. |
| Open redirect or sensitive redirect query | Configuration-only destination, HTTPS and exact-host allow-list, query/fragment/credential rejection, safe slug grammar, and approved agent mapping | Vendor URL/map approval and controlled operational update process. |
| Contact form becomes a mortgage application or abuse target | Explicit field allow-list, extra/control/sensitive-field rejection, length limits, prominent/adjacent UI warnings, zero-length automation trap, and bounded direct-peer rate limiter that fails closed | Legal/privacy approval of draft wording; deployment-level aggregate limiting, trusted-proxy design, monitoring, and tuning before production. |
| Caller rewrites consent evidence | Immutable server registry owns exact draft engineering wording versions, privacy version, source, and capture source; override fields are forbidden | Final legal/privacy wording and immutable version approval. |
| Consent bundled with service or withdrawal damages service evidence | Required service acknowledgement, separately optional marketing record, row-locked/idempotent admin withdrawal, and safe first-withdrawal audit | Customer-facing withdrawal channel/process, retention/deletion policy, and concurrency integration test on PostgreSQL. |
| Lead/contact data leaks through admin URLs or caches | Server-protected layout, FastAPI `require_admin`, nonlocal AAL2, no-store API/server fetch, safe page/status URL filters only, bounded response | Browser/proxy cache probes and production access review. |
| Unauthorized lifecycle/publication change | Backend transition maps, admin role/AAL2, publication evidence, application-specific candidate withdrawal, audit event; premature Phase 1D candidate transitions are unmounted | Phase 1D review/decision and activation-gate implementation after policy approval. |
| Tokens or personal payloads leak through logs/audits | Structured request logs contain method/path/status/IDs only; recruitment audits contain safe IDs, lifecycle/source/category/decision/version values only and exclude answers, contacts, filenames, tokens, URLs, and contents | Central log pipeline tests and redaction review. |
| Unsafe deployment configuration | Pydantic startup validation rejects local storage, dev auth, debug, wildcard/loopback/non-HTTPS origins, missing R2, and missing admin MFA outside local | Deployment-policy test in selected hosting platform. |
| Audit evidence altered | No general update/delete API; append-oriented service | Database privileges, retention, immutable export/storage decision. |

## Abuse cases explicitly excluded

The platform has no borrower application, mortgage underwriting, credit, lender-submission, commission, payroll, or custom signing model. Adding those fields or flows requires scope and threat-model change control.
