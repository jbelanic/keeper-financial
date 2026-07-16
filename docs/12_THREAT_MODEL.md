# Phase 1C Threat Model Summary

This is an engineering threat model, not a legal or compliance certification.

## Assets and trust boundaries

- Public content crosses an untrusted browser/server boundary.
- Supabase establishes external identity; the FastAPI/database boundary grants application authorization.
- Candidate and onboarding data is personal; candidate files and executed agreements are restricted.
- PostgreSQL holds roles, lifecycle, consent, and audit evidence.
- Local filesystem is test/development-only. Private local MinIO is the live object boundary.
- Local ClamAV is a separate container trust boundary; mortgage application, CRM, e-signature, and email remain provider boundaries.

## Primary threats and controls

| Threat | Phase 0 control | Remaining work |
|---|---|---|
| Valid token used as automatic portal access | JWT verification plus verified local identity, active user, role, relationship, lifecycle, and MFA policy | Session revocation integration and operational access review. |
| Candidate accesses another application or file | Posting-specific local relationship, opaque UUID, ownership check on read/save/submit/withdraw/upload/list/download, random object key, application linkage, AAL2 for restricted documents, safe `404` cross-owner behavior, audit event | Local Supabase/MinIO adversarial integration and production access review. |
| Public/private object exposure | No public object route or URL, local-only filesystem guard, private MinIO S3 adapter, short signed retrieval | MinIO bucket-policy review and live probe. |
| Unsafe file | Bounded reads; extension, declared MIME, libmagic MIME, and structural agreement; Pillow decompression-bomb limits; strict PDF parsing; ClamAV `INSTREAM` before persistence; bounded socket protocol/timeouts; safe scan audits; non-clean download denial | Signature freshness/quality monitoring, adversarial corpus testing, and ongoing parser/ClamAV patching. Scanning reduces risk but cannot prove a document benign. |
| Clamd abused as an unauthenticated scan oracle | Both upload routes require an active candidate role and AAL2; the scan-only route never persists bytes; clamd is reachable only on the Compose network and host loopback | Any local process can reach the loopback TCP port; preserve host access controls and never publish 3310 on a public interface. |
| Verified token self-provisions privileged access | Dedicated published-posting start boundary validates signed verified subject/email, rejects link conflicts, grants only candidate role, creates only candidate/application relationships, and remains atomic/idempotent | Local Supabase end-to-end and account-recovery/session-revocation tests. |
| Candidate changes posting, privacy evidence, lifecycle, or submitted answers | Extra-forbid typed schemas, server-owned source snapshot/schema/disclosure/revision/state/timestamps, row locks and revision checks, immutable submitted questionnaire | Operational review of retention/deletion and future controlled reopen design in Phase 1D. |
| Draft/closed/archived posting becomes public | Explicit lifecycle map, published-only indexed queries, direct-slug indistinguishable `404`, plain-text bounded fields, admin role/AAL2, publication actor/time/audit | Production cache/proxy probes and operational approval process. |
| Open redirect or sensitive redirect query | Configuration-only destination, HTTPS and exact-host allow-list, query/fragment/credential rejection, safe slug grammar, and approved agent mapping | Vendor URL/map approval and controlled operational update process. |
| Contact form becomes a mortgage application or abuse target | Explicit field allow-list, extra/control/sensitive-field rejection, length limits, prominent/adjacent UI warnings, zero-length automation trap, and bounded direct-peer rate limiter that fails closed | Legal/privacy approval of draft wording; deployment-level aggregate limiting, trusted-proxy design, monitoring, and tuning before production. |
| Caller rewrites consent evidence | Immutable server registry owns exact draft engineering wording versions, privacy version, source, and capture source; override fields are forbidden | Final legal/privacy wording and immutable version approval. |
| Consent bundled with service or withdrawal damages service evidence | Required service acknowledgement, separately optional marketing record, row-locked/idempotent admin withdrawal, and safe first-withdrawal audit | Customer-facing withdrawal channel/process, retention/deletion policy, and concurrency integration test on PostgreSQL. |
| Lead/contact data leaks through admin URLs or caches | Server-protected layout, FastAPI `require_admin`, live-production AAL2, no-store API/server fetch, safe page/status URL filters only, bounded response | Browser/proxy cache probes and production access review. |
| Unauthorized lifecycle/publication change | Backend transition maps, admin role/AAL2, publication evidence, application-specific candidate withdrawal, audit event; premature Phase 1D candidate transitions are unmounted | Phase 1D review/decision and activation-gate implementation after policy approval. |
| Tokens or personal payloads leak through logs/audits | Structured request logs contain method/path/status/IDs only; recruitment audits contain safe IDs, lifecycle/source/category/decision/version values only and exclude answers, contacts, filenames, tokens, URLs, and contents | Central log pipeline tests and redaction review. |
| Unsafe deployment configuration | Pydantic production validation rejects local-file storage, dev auth, debug, wildcard/remote origins, missing MinIO/Supabase settings, non-Compose database/storage hosts, and missing admin MFA | Live local-host deployment-policy probe and host hardening review. |
| Audit evidence altered | No general update/delete API; append-oriented service | Database privileges, retention, immutable export/storage decision. |

## Abuse cases explicitly excluded

The platform has no borrower application, mortgage underwriting, credit, lender-submission, commission, payroll, or custom signing model. Adding those fields or flows requires scope and threat-model change control.
