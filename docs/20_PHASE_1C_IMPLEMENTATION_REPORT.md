# Phase 1C Recruitment Implementation Report

**Date:** 2026-07-15  
**Branch:** `feature/phase-1c`  
**Immutable base / current HEAD:** `18167272b19204f8746fcd6d0180e39fdb9e7640`  
**Base subject:** `docs: approve Phase 1C candidate application policy`

## Outcome

Phase 1C recruitment is implemented and locally engineering-complete for REC-001–REC-005 and CAN-001–CAN-009. PostgreSQL is authoritative; FastAPI/Pydantic remains the API-contract source; the public, candidate, and administration workflows are present in the Next.js application; and the approved policy in `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md` is unchanged.

No implementation work was committed, pushed, merged, deployed, or placed on another branch. Phase 1D review/onboarding/activation operations and Phase 1E agent-profile expansion were not implemented. The pre-existing broad candidate-status transition router is no longer mounted, so its premature operations return 404.

## Requirement disposition

| Requirement | Disposition and evidence |
| --- | --- |
| REC-001 | Complete. AAL2 brokerage administrators can create, edit, publish, close, and archive bounded plain-text postings through an explicit lifecycle service and admin API/UI. There is no hard delete. |
| REC-002 | Complete. Anonymous list/detail API and `/careers` pages expose published postings only, with deterministic ordering and bounded pagination. |
| REC-003 | Complete. A verified Supabase identity can start an application only against a currently published posting through the narrow provisioning boundary. |
| REC-004 | Complete. Every attempt retains the posting UUID plus immutable slug, title, and version snapshots; the FK is `ON DELETE RESTRICT`. |
| REC-005 | Complete. Draft, closed, archived, unknown, malformed, and missing slugs are indistinguishable 404 responses and never enter the public list. |
| CAN-001 | Complete. Registration and callback use the installed Supabase SDK; the callback exchanges the provider session and invokes controlled application start. |
| CAN-002 | Complete. General bearer authentication still resolves only mapped, active, verified local principals. Verified-but-unmapped identities are denied everywhere except explicit application start. |
| CAN-003 | Complete. Candidates read/save only their posting-specific drafts. Typed bounded schemas, ownership predicates, row locks, and expected revisions are enforced. |
| CAN-004 | Complete. Submission validates all approved required sections and confirmations server-side, freezes content, records the disclosure evidence, advances status, adds one history row, and writes one audit event transactionally. |
| CAN-005 | Complete. Submitted and withdrawn questionnaire content is read-only; no reopen or information-request operation exists. |
| CAN-006 | Complete for local/test engineering. Candidate documents require AAL2 and ownership, are bounded and signature-validated, use private random keys, begin pending/quarantined, and are downloadable only when clean. Nonlocal use fails closed without a real scanner. |
| CAN-007 | Complete. Candidate status is application-specific and text-visible; the Phase 1C controlled message list is empty. |
| CAN-008 | Complete. Candidate schemas structurally omit internal reasons, internal notes, actors, and audit metadata. |
| CAN-009 | Complete under the approved policy. Draft/submitted applications may be explicitly withdrawn; prior records remain readable, questionnaires and new uploads become unavailable, and a new same-posting attempt is allowed only while the posting remains published. |

## Delivered routes and user interfaces

FastAPI routes:

- `GET /api/v1/recruitment/postings`
- `GET /api/v1/recruitment/postings/{slug}`
- `POST /api/v1/recruitment/postings/{slug}/applications/start`
- `GET|POST /api/v1/admin/recruitment-postings`
- `PATCH /api/v1/admin/recruitment-postings/{posting_id}`
- `POST /api/v1/admin/recruitment-postings/{posting_id}/{publish|close|archive}`
- `GET /api/v1/candidate/privacy-disclosure`
- `GET /api/v1/candidate/applications`
- `GET /api/v1/candidate/applications/status`
- `GET|PATCH /api/v1/candidate/applications/{application_id}`
- `POST /api/v1/candidate/applications/{application_id}/submit`
- `POST /api/v1/candidate/applications/{application_id}/withdraw`
- `GET|POST /api/v1/candidate/applications/{application_id}/documents`
- `DELETE /api/v1/candidate/applications/{application_id}/documents/{document_id}`
- `GET /api/v1/documents/{document_id}/download`

Web workflows:

- dynamic public `/careers` and `/careers/[slug]` publication views;
- `/auth/register` and posting-bound `/auth/callback` provisioning;
- candidate application list, typed draft editor, persistent progress, save state, review, disclosure, submit, status, document, and withdrawal controls;
- `/admin/recruitment` posting administration;
- semantic headings/landmarks, keyboard-native controls, linked and focused error summaries, live upload/save announcements, confirmation focus restoration, reduced-motion support, practical 320-CSS-pixel reflow, and text in addition to status colour.

These checks are accessibility regressions, not a claim of formal WCAG certification.

## Identity, privacy, document, audit, and logging controls

Supabase proves external identity only. The server reads signed `sub`, verified provider email, verification state, and AAL; request bodies cannot choose identity, role, candidate, posting state, schema/disclosure version, application state, revision, or timestamps. Provisioning atomically and idempotently creates or links only `User`, `UserIdentity`, the candidate role, `Candidate`, and one posting-specific `CandidateApplication`. Subject/email conflicts, inactive users, noncandidate roles, duplicates, and concurrent retry conflicts fail safely.

The exact server-owned disclosure version is `candidate-privacy-disclosure-2026-07-15-v1`. Its approved collection purpose, categories, access, policy-controlled retention language, service-provider use, contact, and consequences of omission are served and displayed before submission. Submission stores the version and acknowledgement timestamp independently from marketing consent.

The only document categories are `resume` and `cover_letter`; neither is required. PDF, DOC, and DOCX extension, declared MIME, and magic/signature must agree. Files are streamed with a 10 MiB cap, sanitized metadata, SHA-256, detected MIME, category, scan status, and timestamps. Bytes remain in private storage under random keys. The local/test scanner is explicitly labelled nonproduction. Nonlocal uploads fail closed when scanning is unavailable; quarantined/non-clean and missing objects do not download; post-storage database failures trigger orphan deletion. Downloads reauthorize owner or AAL2 administrator access and return `private, no-store` and `nosniff` headers.

Required Phase 1C audit event types are implemented. Safe metadata is restricted to IDs, lifecycle states, posting source/version, document category, and scan decision/source. Application answers, contact values, filenames, raw payloads, tokens, signed URLs, and object contents are not recorded. Live audit and container-log probes found zero matches for the synthetic email, filename, answer text, tokens, signed-URL keys, or document content.

## Database and generated contracts

Migration `20260715_0003_phase_1c_recruitment.py` follows `20260714_0002`. It adds posting lifecycle evidence/indexes, posting-specific application attempts and immutable provenance, typed application columns and repeat-entry tables, application-specific status history, strict candidate-document linkage/category/detected-MIME fields, uniqueness and partial concurrency indexes, and restrictive provenance deletion. It deliberately aborts rather than inventing linkage/provenance for incompatible legacy records.

Normal PostgreSQL evidence:

- `make migrate`: passed;
- `alembic current`: `20260715_0003 (head)`;
- `alembic check`: `No new upgrade operations detected.`

An isolated database named `keeper_phase1c_validation_20260715` was created independently of the normal volume, upgraded through `20260714_0001 -> 20260714_0002 -> 20260715_0003`, checked at head with no drift, used for the PostgreSQL concurrency proof, and then dropped. The normal volume was never deleted or replaced.

OpenAPI and TypeScript generation passed twice with identical hashes:

- `packages/contracts/openapi.json`: `1962cb02947f4e13bd9063321e64ccb4af767813166c42fb297dbafe6109e165`
- `packages/contracts/src/generated.ts`: `af21899636abb454e7b491665a31f81f0aecc5a782fb0554e710dd2da6b7c152`

Public operations are anonymous in the contract; candidate and administration operations declare bearer security and explicit error responses. Contract tests prove Phase 1C path presence, security, and the absence of internal candidate fields.

## TDD and validation evidence

Vertical slices were driven from expected RED to focused GREEN before affected regressions. Initial route tests failed for 13 posting cases, 13 candidate-application cases, and 14 document cases before implementation. Additional REDs covered exact disclosure delivery, scan rejection retention, local storage permission failure, save-before-review sequencing, careers publication behavior, registration/callback, candidate application/document accessibility, and admin lifecycle UI. Confirmed defects were fixed without weakening guards.

Final command results:

| Gate | Exact result |
| --- | --- |
| Runtime/tool versions | Node `v24.18.0`; npm `12.0.1`; Python `3.14.4`; Docker `29.5.3`; Compose `v5.1.4`; Git `2.53.0` |
| Install/dependency shape | `npm ci` passed; `pip check` passed; Vitest `3.2.6`, Next `16.2.10`, PostCSS `8.5.19` present |
| Formatting/lint/type | Prettier, ESLint, TypeScript, Ruff check/format, mypy (43 source files), and compileall all passed |
| Web tests | 19 files, **69 passed** |
| API tests | **128 passed, 1 skipped, 1 warning** in 9.31 s |
| PostgreSQL concurrency | **1 passed** against the isolated PostgreSQL database; proves two concurrent starts and submissions yield one application, history, and submission audit |
| Build | Next.js production build passed; 34 pages generated |
| Contracts | Generation, nonempty checks, contract formatting/typecheck, and two-run hash comparison passed |
| Docker | `docker compose config`, full API/web build, `up -d`, migrations, and service startup passed; database and API reported healthy |
| Smoke | `/health`, `/health/db`, `/careers`, synthetic published list/detail, all nonpublic slug negatives, anonymous denial, identity-only denial, start/save/submit/status/upload/withdraw, post-withdraw read/no-new-upload, cross-candidate denial, Phase 1D 404, and safe audit/log probes passed |

The full API suite's one skip is the opt-in PostgreSQL concurrency test when `PHASE1C_TEST_DATABASE_URL` is absent; the same test passed separately with that variable pointing to the isolated database. The one warning is the upstream Starlette `TestClient` deprecation for its current `httpx` integration. A `-W error` diagnostic confirmed that exact dependency warning before collection; it is not suppressed or relabelled.

## Security scan evidence

| Scanner | Version and result |
| --- | --- |
| Gitleaks | Installed build reports `version is set by build process`; required redacted repository scan passed with no leaks across 6 commits |
| Trivy | `0.52.2`; memory-conscious filesystem vulnerability/secret/misconfiguration scan completed with no HIGH/CRITICAL finding; `start-hermes.sh` was explicitly excluded |
| Bandit | `1.9.3` on Python `3.12.3`; required high-severity and additional unfiltered scans both found **0 issues**, with no `#nosec` suppressions |
| Semgrep | Installed `1.56.0` could not parse a current registry severity; per the execution brief, isolated `/tmp` Semgrep `1.169.0` ran single-threaded with 1024 MiB/60 s bounds: 156 targets, 452 rules, **0 findings** |
| npm audit | `--audit-level=high`: **0 vulnerabilities** |
| pip check | No broken requirements |
| diff whitespace | `git diff --check`: passed |

Gitleaks and Trivy reported no leaks/findings; no result was suppressed or downgraded. The only scanner compatibility failure was replaced by the expressly permitted isolated Semgrep environment and is retained here as evidence.

## Owner inputs, external dependencies, and limitations

All Phase 1C product gates resolved by the approved policy were implemented exactly: questionnaire/sections, required and optional fields, application cardinality/reapplication, post-withdrawal access, document categories/rules, disclosure wording/version, and candidate MFA.

Remaining external inputs do not block local engineering but do block production operation where applicable:

- no production malware-scanner provider is approved; nonlocal document upload therefore fails closed;
- hosted Supabase and R2 credentials/configuration are not supplied or invented;
- no email provider/notification behavior is implemented;
- no real recruitment posting is supplied; seeds are conspicuously synthetic;
- legal retention periods remain policy-owned; the disclosure promises no invented fixed period.

Phase 1D candidate review, notes, requests, decisions, onboarding/activation, Phase 1E profile work, Phase 1F origination, production hosting/monitoring/backups, and formal accessibility certification remain deferred.

The implementation author completed a distinct final read-only security/scope review of lifecycle maps, publication filtering, provisioning conflicts, ownership, concurrency, provenance, quarantine/scanner/orphan behavior, contract leakage, audit minimization, migration drift, Phase 1D/1E boundaries, and accessibility semantics, with no unresolved defect found. In accordance with the working agreement and the instruction not to invoke another coding agent recursively, the Hermes coordinator remains the separate non-author verifier after this handoff; this report does not misrepresent the author's review as independent verification.

## Final repository state and diff inventory

At report generation, the branch remains `feature/phase-1c` and HEAD remains the immutable base `18167272b19204f8746fcd6d0180e39fdb9e7640`. The worktree intentionally contains only uncommitted Phase 1C changes: 36 tracked modified paths and 36 untracked files after adding this report. Tracked diff before untracked-file accounting is 5,128 insertions and 574 deletions across 36 paths; the generated contracts account for most of that volume.

Intentional inventory:

- configuration/runtime: `.env.example`, `compose.yaml`;
- API model/config/router/integration changes: `apps/api/src/keeper_api/{api/router.py,api/routes/documents.py,core/config.py,main.py,models/domain.py,services/auth.py,services/storage.py}`;
- new API Phase 1C routes/schemas/services: recruitment, candidate applications/privacy, candidate documents/files/scanner;
- database/seed: `20260715_0003_phase_1c_recruitment.py`, `apps/api/scripts/seed_local.py`;
- API tests: recruitment, candidate applications, candidate documents, OpenAPI, integrations/health, and isolated PostgreSQL concurrency;
- web/UI: public careers, registration/callback, candidate application/status/document/withdrawal, admin recruitment, portal API helpers, navigation, CSS, and shared accessible controls;
- web tests: publication, recruitment, registration/provisioning, candidate application/document, admin recruitment, routing, and accessibility-focused assertions;
- generated contracts: `packages/contracts/openapi.json`, `packages/contracts/src/generated.ts`;
- documentation: `README.md`, delivery/acceptance/environment/threat/API/test/limitation/local-development documents, and this report.

`docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md` has no diff. The known ignored `start-hermes.sh` is not part of status or the diff and was not opened, edited, formatted, moved, staged, scanned, remediated, or committed. Its final SHA-256 is verified separately at handoff. No secret-bearing `.env` file was read.
