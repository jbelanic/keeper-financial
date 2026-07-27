# Candidate Authentication and Onboarding Completion Implementation Report

**Date:** 2026-07-18  
**Branch:** `fix/candidate-auth-onboarding-completion`  
**Starting HEAD:** `f381dec4c08c2d50c452ed892fd60d9c7f287215`  
**Required ancestry:** Phase 1D `6349c16`, Phase 1E `384246c`, ClamAV `e9d9f65`  
**Disposition:** base remediation, local admin AAL2 ceremony, genuine local
Supabase/Mailpit candidate entry, three-run Firefox login stabilization,
in-place save feedback, realistic PDF/DOCX document validation/upload, and
responsive homepage validation are complete. The worktree is not ready to
commit until the fresh genuine
administrator information-request send passes.

## Scope and confirmed root causes

The implementation was inspected from published posting through Supabase
registration/password sign-in, confirmation callback, local application start,
portal authorization, review, assignment, and candidate onboarding.

The confirmed defects were:

- the posting exposed only registration and generic sign-in discarded posting
  intent;
- callback was the only browser path that invoked the approved posting-bound
  provisioning operation;
- SSR cookie helpers existed without protected-request refresh orchestration or
  realistic callback/cross-request evidence;
- onboarding pages were not discoverable in candidate/admin navigation;
- review state and decisions mutated a candidate-wide status instead of the
  selected posting-specific attempt;
- assignment did not prove the exact conditionally-selected application or an
  active plan; and
- acknowledgement accepted an existing version without an assignment/version
  authorization relationship; and
- the seeded local administrator identity used a documented placeholder subject
  that did not match the real local Supabase Auth user, and no approved linking
  command or browser TOTP ceremony existed; and
- the posting-bound application-start dependency treated a genuine confirmed
  Supabase user as unverified because it expected top-level `email_verified` or
  `email_confirmed_at` JWT claims that the local Supabase token did not contain.
  The candidate bearer was forwarded correctly, ES256/JWKS, issuer, audience,
  expiry, and token parsing had already passed, and no existing local mapping,
  candidate role, or `Candidate` dependency was applied. The resulting explicit
  verified-identity rejection was the exact source of the observed `403`.
- The shared candidate layout fetched the full protected onboarding dashboard
  on every server render merely to decide whether to show one navigation item.
  A permanent no-assignment/authorization result was collapsed to `null`, so
  Next navigation, prefetch, and rerender requests could repeat the same full
  projection with no stable distinction from a transient failure.
- Candidate validation policy was correct, but only partial HTML attributes
  described it and non-success browser JSON was discarded. Valid `422` details
  became one generic error instead of field-linked guidance.
- Candidate documents stated that AAL2 was required but did not inspect factors
  or offer enrollment/challenge. The MFA return allow-list admitted only portal
  roots and did not refresh and reconfirm AAL2 before continuing.
- Information requests already carried `application_id`, but the admin UI kept
  the action enabled for a selected `application_submitted` attempt. The source
  lifecycle allows the operation only for `under_review` or `interview`; the
  tested candidate also had a separate draft application, so candidate-wide
  inference was unsafe. Interview-specific `409` wording was stale or
  incorrectly reused runtime text and was not an acceptable operation error.
- Candidate/post-login hard navigation streamed the implicit root
  `loading.tsx` fallback even after the access, application, disclosure, and
  availability requests completed. The long-running default Turbopack process
  had grown to roughly 3 GiB and repeatedly failed its HMR WebSocket; the final
  RSC/hydration commit could then wait for incidental browser work. There were
  no application focus, visibility, resize, print, or tab event handlers to
  complete the state.
- Draft save had only a top-of-page status. The same shared error effect also
  focused the top summary for save-only validation/API errors, while disabling
  the focused button during a request caused genuine Firefox to drop focus.
- The visible application-section strip was sticky, noninteractive text and
  obscured long-form content.
- AAL2 document metadata required an ambiguously labelled manual load button
  that disappeared without a list/empty/error explanation. Upload errors
  collapsed validation, malware, scanner, and storage failures.
- The genuine upload `503` first occurred before storage because a host-run API
  inherited Compose-only `clamav` and `minio` DNS names. After the scanner
  endpoint was corrected, the bounded category advanced to storage unavailable:
  ignored host S3 credentials did not match the running MinIO credentials,
  whereas Compose explicitly maps them. Scanner-unavailable audit evidence was
  bounded and no `CandidateDocument` metadata existed; route ordering proves
  object storage was not invoked for those scanner failures.
- The public hero and recruitment blocks removed the centered container maximum
  and right padding, then added a second viewport-derived left offset inside
  that already centered geometry. A tall stretched cover box compounded the
  right-side focal crop and made the hero/trust/header alignment diverge.
- Candidate document validation rejected common files before ClamAV. The PDF
  reader required every byte after the last `%%EOF` to be whitespace, rejecting
  otherwise readable PDFs with bounded printable PDF comment lines. The DOCX
  layout validator rejected ZIP general-purpose flag `0x08`, although standard
  office output used valid data descriptors (ten entries in the reproduced
  file). The live audits retained only `malformed`; the representative common
  files reproduced the exact checks without using private candidate data.

No unresolved owner product or security decision was found. The current source
of truth already approved application-specific lifecycle, conditional-selection
assignment, exact-version evidence, and readiness-only activation. The older
Phase 1C reconciliation statement that broadly described callback completion is
historical evidence and does not override the current readiness assessment.

## Implemented behavior

### Authentication, session, and provisioning

- Published postings expose create-account and existing-user sign-in actions.
- Registration and sign-in server pages accept only a scalar slug and prove it
  through the published-posting API before rendering a posting-bound flow.
- Registration confirmation callback and posting-bound password sign-in both
  establish the Supabase SSR session and invoke only
  `POST /api/v1/recruitment/postings/{slug}/applications/start`.
- Safe posting context survives bounded authentication/provisioning errors and
  retries. A posting that no longer exists as published is discarded.
- Generic sign-in remains non-provisioning. A Supabase identity without local
  authorization remains denied by `/api/v1/auth/access?area=candidate`.
- The start operation remains atomic and idempotent. The database unique
  boundaries and posting lock prevent duplicate user identity, role, candidate,
  nonterminal attempt, and start-audit evidence under retries/concurrency.
- Posting start now validates the signed token first and then asks local
  Supabase Auth `/user`, using the same bearer and browser-safe public anon key,
  to confirm the exact UUID subject, signed email, and authoritative
  `email_confirmed_at`. It does not trust user-editable metadata and requires no
  pre-existing local mapping. Provider unavailability fails closed with a
  bounded `503`; no service-role credential is used.
- Next.js request proxying validates/refreshes Supabase sessions for auth and
  protected portal paths and forwards rotated/deleted cookies. Server access
  helpers ask Supabase for the current user before reading the session token.
- A local-only operator script transactionally replaces only the known seeded
  admin placeholder with an explicitly supplied Supabase UUID. It requires the
  existing active user, exact `brokerage_admin` role, and existing Supabase
  identity; it grants or creates none of them.
- Generic `/auth/sign-in?returnTo=/admin` is now discoverable but remains
  non-provisioning. Successful authentication continues through a browser TOTP
  enrollment/challenge page, while API/PostgreSQL mapping and AAL2 remain the
  independent authorization boundary.
- link_local_admin_identity.py successfully linked the real local Supabase subject.
- MFA enrollment initially exposed a trailing-whitespace QR data-URI defect.
- The QR source was normalized and rendered successfully.
- A fresh TOTP factor was enrolled.
- The admin signed in with AAL2.
- /admin, /admin/candidates, and /admin/onboarding were reachable.
- Generic sign-in still does not grant admin access.
- Final activation remains unimplemented.
- General Alembic drift remains unresolved.

### Application lifecycle and onboarding

- Review queue entries are posting-specific attempts. Detail, interview,
  information request, decision, and assignment operations require the exact
  `application_id`; row locking and transition maps preserve cross-application
  isolation, reasons, history, and audit evidence.
- A later start reuses every nonterminal same-posting attempt. Only withdrawn or
  declined attempts permit a new immutable attempt number.
- Assignment requires the selected attempt to be `conditionally_selected` and
  the selected plan to be active. Failure does not supersede an existing valid
  assignment.
- Assignment records its application and generation, binds task instances to
  that assignment, and snapshots exact currently issued, non-superseded
  controlled-document versions.
- Candidate acknowledgement requires ownership, the current assignment, the
  exact assigned version, an issued/non-superseded version, and an idempotent
  evidence row. Arbitrary, unassigned, cross-candidate, and ineligible versions
  fail closed.
- `activation_ready` requires a current application-bound assignment, all
  required assignment tasks, all required exact assigned acknowledgements, and
  every allow-listed gate. It performs no activation and creates no agent role.
- Candidate navigation discovers onboarding only when its protected dashboard
  is authorized. Authorized admins receive a navigation entry. Direct server
  and API authorization remains authoritative.

### Focused browser-completion behavior

- The shared candidate shell calls only
  `GET /api/v1/candidate/onboarding/availability`. No assignment returns
  `available=false`; the direct dashboard returns an empty successful
  projection with `activation_ready=false`. The shell does not call the full
  dashboard, permanent failures are not automatically retried, and the direct
  page offers only an explicit transient retry.
- The application form mirrors every approved Phase 1C material requirement,
  preserves draft values, uses canonical month controls, clears ineligible
  referral detail, performs a client preflight without replacing server
  validation, and safely maps bounded `422` locations to an announced linked
  summary and exact field errors.
- Candidate documents inspect current assurance and verified TOTP factors
  before any private metadata request. Enrollment/challenge reuses the existing
  ceremony, removes incomplete factors before replacement, refreshes the
  session, reconfirms AAL2, and returns only to an exact allow-listed candidate
  application `#documents` anchor. Candidate MFA creates no admin authorization.
- Admin review visibly retains opportunity and attempt. Information request is
  disabled until the selected exact application is `under_review` or
  `interview`, sends that `application_id`, transitions only it, and presents
  operation-specific conflict wording. Candidate status exposes only open
  bounded request messages for the owning application, not interview notes.
- Global/public implicit loading files are removed from hard navigation. Portal
  server/API authorization fetches have a bounded ten-second abort, and pages
  terminate in their existing content or safe error/retry state. Host web
  development is pinned to Next webpack instead of the degraded default
  runtime. No focus/visibility/resize hook, arbitrary delay, or polling was
  added to application behavior.
- Save now has an action-local `aria-live="polite"` region and explicit
  saving/saved/validation/network/conflict states; the button temporarily reads
  Saving/Saved. Duplicate submission remains disabled, valid values and scroll
  are retained, and focus returns to the same save control after Firefox drops
  it while the button is disabled. The top-level status remains as secondary
  persistent context.
- The section strip is disposed as a one-time informational outline in normal
  document flow. It is not exposed as navigation and is neither sticky nor
  fixed.
- Confirmed AAL2 automatically loads document metadata into loading, list,
  explicit **No documents uploaded yet**, or bounded retry states. Successful
  upload refreshes the authoritative list, announces the clean decision,
  preserves category, resets only the file input, and blocks duplicates.
  Invalid/unsupported input, malware, scanner outage, storage outage, and
  authorization/MFA have distinct allow-listed messages.
- `make api-dev` now uses a local launcher that maps ignored MinIO values into
  the host S3 adapter and selects loopback MinIO/ClamAV endpoints without
  printing secrets. Compose keeps explicit internal `minio:9000` and
  `clamav:3310`; scanner exposure remains loopback-only and fail-closed.
- The homepage hero/recruitment compositions again use the shared centered
  max-width container, symmetric padding, bounded aspect-ratio media, and an
  intentional hero focal position. No zoom- or screenshot-specific offset is
  used.
- PDF validation now requires a recognized header/version, a final EOF, only a
  bounded printable PDF-comment tail, non-encrypted structural readability,
  and at least one page, using tolerant parser mode for common producer
  variations. Binary/polyglot tails, fake headers, truncation, encryption, and
  unreadable structure remain rejected.
- DOCX validation accepts official or bounded ZIP-family libmagic detection
  only after strict OPC/WordprocessingML proof. Standard signed/unsigned data
  descriptors are checked against central-directory CRC/compressed/expanded
  sizes; entry/path/count/compression/ratio/expanded-size/XML limits,
  encryption, macro, duplicate-name, required-part/content-type, relationship,
  and archive-boundary checks remain fail closed. Legacy DOC remains a narrow
  Word compound-file check rather than arbitrary OLE acceptance.
- Candidate upload responses/UI distinguish safe extension, declared/detected
  MIME, PDF/DOCX/DOC structure, size, malware, scanner, and storage categories.
  Validation precedes ClamAV and clean scanning precedes MinIO/metadata.

### Candidate field-validation matrix

| Field/group                | Phase 1C rule                                                                                                      | Browser correction; server remains authoritative                                                        |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| Given/family name          | Required for submission; 1–70 each                                                                                 | Required-labelled text controls, max 70, linked errors.                                                 |
| Preferred name             | Optional; max 70                                                                                                   | Optional label and maximum hint/control.                                                                |
| Verified email             | Required server-owned identity value                                                                               | Read-only; omitted from editable authority.                                                             |
| Phone                      | Required; max 32 input, leading `+`, 8–15 normalized digits                                                        | `type=tel`, exact hint/example, client preflight.                                                       |
| City/region                | City required 1–100; region optional max 100                                                                       | Required/optional labels, max limits, linked errors.                                                    |
| Country                    | Required ISO alpha-2                                                                                               | Two-character control, `CA` example, client format check.                                               |
| Preferred contact          | Required approved enum                                                                                             | Required select containing only approved values.                                                        |
| Available from             | Optional ISO date                                                                                                  | `type=date` and `YYYY-MM-DD` fallback hint.                                                             |
| Referral source/detail     | Source optional enum; detail max 120 only for employee/agent referral or Other                                     | Conditional control; any other selection clears state and payload.                                      |
| Interest statement         | Required for submission; 100–2,000                                                                                 | Visible range, live count, preserved controlled value, client preflight.                                |
| Relevant experience        | Optional; max 2,000                                                                                                | Optional label, maximum/live count, sensitive-data warning.                                             |
| Employment (0–5)           | Employer/title 1–160; start `YYYY-MM`; current excludes end; past end required/not before start; summary max 1,000 | Accessible repeat controls, `type=month`, canonical payload, conditional end, entry-linked errors.      |
| Education (0–3)            | Institution/program 1–160; optional year 1900–current                                                              | Accessible repeat controls, bounded numeric year, entry-linked errors.                                  |
| Privacy/accuracy           | Both required only for final submission                                                                            | Explicit submission-only checkboxes; incomplete draft remains saveable.                                 |
| Revision/provenance/status | Server-owned; expected revision required                                                                           | Distinct save/review/submit feedback; stale `409` fails closed; unknown/server fields remain forbidden. |

### Candidate document format-validation addendum

The prior live `422` responses occurred before scanner construction and object
storage. Safe audit aggregation for the recent rejection window showed three
`malformed` validation decisions, zero scan decisions, and zero new candidate
document metadata rows. The old single `malformed` code cannot retrospectively
distinguish its internal PDF subcheck; bounded local reproduction established
the two format-specific defects without reading or retaining a candidate file:

- the existing strict PDF EOF-tail check rejected 8 of 12 readable installed
  common PDF samples solely because printable PDF comment lines followed
  `%%EOF`; and
- a standard office DOCX had the official declared and detected DOCX MIME but
  was rejected at the ZIP-layout flag check because ten valid entries used data
  descriptors. With only that check bypassed, all existing OPC and
  WordprocessingML checks passed.

The corrected acceptance matrix is:

| Format | Extension/declared MIME                      | Detected MIME                                       | Structural decision                                                                                                                                                                                   |
| ------ | -------------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PDF    | `.pdf` / `application/pdf`                   | `application/pdf`                                   | Recognized `%PDF-` version, final EOF with at most 4 KiB of printable PDF comments/whitespace, readable non-encrypted structure, and at least one page.                                               |
| DOC    | `.doc` / `application/msword`                | `application/msword` or `application/x-ole-storage` | Existing Word compound-file signature, `WordDocument` FIB, and selected `0Table`/`1Table`; arbitrary OLE remains rejected.                                                                            |
| DOCX   | `.docx` / official Office Open XML Word MIME | official MIME or bounded ZIP-family MIME            | Exact ZIP boundaries/data descriptors plus required OPC/Word parts, content types and relationships; bounded entries/XML/expansion/ratio; safe paths; supported compression; no encryption or macros. |

Candidate API details are now safe stable categories:
`unsupported_extension`, `declared_mime_mismatch`,
`detected_mime_mismatch`, `pdf_structure_invalid`,
`docx_structure_invalid`, `legacy_doc_invalid`, `file_too_large`,
`malware_detected`, `scanner_unavailable`, and `storage_unavailable`, with
additional bounded category/name/empty-file input codes. The browser maps each
to concise guidance and never displays parser, scanner, storage, provider, or
object details.

The final opt-in genuine Firefox run used a new synthetic candidate, real
Mailpit/PKCE, browser TOTP challenge, and the actual document controls. One
standard office-generated PDF and one standard office-generated DOCX each
uploaded successfully, announced completion, and refreshed metadata. The same
run uploaded those two formats plus the existing synthetic PDF through the
authenticated API path. The final window contained five `clean` scanner
decisions and five metadata rows: three PDF and two DOCX, all with matching
declared/detected MIME and `scan_status=clean`. The fake PDF and truncated DOCX
returned their distinct structural `422` categories, produced rejection audits,
and added no metadata. Aggregate private-object inspection matched seven recent
clean metadata rows to seven recent private objects (the total includes two
clean browser uploads completed during bounded test-harness diagnostics); no
rejected upload added an object. Unauthenticated download and administrator
access remained denied, and deterministic tests retain the cross-candidate and
AAL2 matrices. No credential, factor secret, candidate identifier, original
file name, object key, provider payload, or document content was emitted in the
test result.

## Data and migration boundary

Forward migration `20260717_0006_candidate_auth_onboarding_completion.py`:

- expands the application lifecycle constraint and nonterminal uniqueness
  predicate;
- stores application-specific interview and information-request provenance;
- links onboarding assignments to applications and task instances to
  assignments;
- creates the exact assignment/document-version join; and
- links acknowledgements to their assignment generation.

Issued migrations were not edited. Existing rows remain nullable where the
correct historical relationship cannot be proved, and new mutation/readiness
paths reject that ambiguity. No guess-based data backfill occurs. The migration
does not include the separate known Phase 1D index/foreign-key `ondelete` drift.

## Security and privacy controls preserved

- Supabase proves identity only; PostgreSQL remains the authorization and
  lifecycle authority.
- Issuer, audience, ES256/JWKS signature, verified-email, local mapping, role,
  lifecycle, ownership, and existing MFA enforcement remain in the API. The
  posting-start exception is deliberately narrower: the externally verified
  identity may be unmapped because that transaction creates the candidate
  mapping; every ordinary portal request still requires PostgreSQL
  authorization.
- No browser-supplied role, candidate, posting record, application state, plan
  eligibility, assignment, or document authorization is trusted.
- Errors are bounded and do not render tokens, cookies, provider payloads,
  internal identifiers, notes, reasons, actors, or audit metadata.
- Private MinIO, fail-closed ClamAV, local-only Studio, and disabled Supabase
  Storage/S3 architecture are unchanged.
- No custom signing, hosted infrastructure, external CRM, borrower financial
  data, automated regulatory claim, or final activation operation was added.

## Test coverage

Focused API tests cover posting-start idempotency/reapplication, application-
specific transition/history isolation, conditional-selection and active-plan
assignment, assignment idempotency/preservation, exact assigned-version
acknowledgement, cross-candidate/superseded denial, readiness, absence of final
activation, migration shape, OpenAPI contracts, and ES256/JWKS verification.

Focused web tests cover both posting actions, scalar/malformed/unpublished
posting rejection, registration/sign-in/callback context, generic
non-provisioning, callback exchange/cookie writes, refresh/expiry behavior,
candidate/admin navigation, and safe recovery errors. An opt-in realistic local
integration test uses synthetic Supabase identities and Mailpit confirmation to
exercise registration, existing-user recovery, fresh-request cookie state,
posting-specific application entry, and optional onboarding entry.

The local admin addendum adds isolated script coverage for placeholder-only
replacement, idempotency, every prerequisite/input refusal, duplicate-subject
protection, non-local refusal, and rollback. Web tests exercise TOTP enrollment,
verified-factor challenge, already-AAL2 handling, bounded provider failure, the
explicit admin return path, and non-provisioning behavior. API tests prove AAL1
admin denial on both the access probe and a protected route, AAL2 admin success,
and candidate/unmapped AAL2 denial.

The browser-completion suite adds stable no-assignment/availability tests,
visible field-policy and canonical month/referral payload tests, safe linked
`422` mapping with value preservation, candidate factor enrollment/challenge
and exact-return tests, post-refresh AAL2 proof, and application-specific admin
information-request lifecycle/mismatch/history/audit/candidate-message tests.

### Genuine-browser TOTP QR follow-up

After the local-only identity link succeeded and the administrator reached the
MFA enrollment page, a genuine browser run exposed a Next.js runtime rejection:
the Supabase-generated inline SVG data URI ended in whitespace/control
characters. The enrollment request had already created an unverified TOTP
factor before rendering failed.

The corrected browser component now applies `trimEnd()` before the QR source is
stored and again at the `Image` boundary, accepts only a nonempty SVG data URI
or structurally bounded raw SVG fallback, and fails closed for empty, malformed,
or non-string provider output. The inline SVG retains explicit dimensions,
accessible alt text, and `unoptimized`; it is never sent through Next.js image
optimization. The approved manual setup-key fallback remains visible only in
the active enrollment view and is never copied into errors or logs.

On entry, every unverified TOTP factor is treated as incomplete. Retry removes
those factors before creating exactly one replacement, disables repeated
enrollment submission while work is pending, and attempts to remove a newly
created factor immediately if its QR source is unusable. If that cleanup cannot
complete, the factor remains tracked for removal on retry. MFA and backend AAL2
requirements are unchanged.

## Validation evidence

Results from the final 2026-07-18 worktree:

| Command/check                                        | Result                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `git diff --check`                                   | Passed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `docker compose config --quiet` using `.env.example` | Passed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `make lint`                                          | Passed: ESLint and Ruff green.                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `make typecheck`                                     | Passed: all TypeScript workspaces and mypy; 55 Python source files.                                                                                                                                                                                                                                                                                                                                                                                                     |
| `make test`                                          | Passed: web 27 files plus one skipped live file; 139 tests passed and 3 opt-in live tests skipped in the ordinary isolated run. API: 334 passed, 2 opt-in tests skipped, 4 warnings.                                                                                                                                                                                                                                                                                    |
| focused candidate-document suites                    | Passed: 90 API tests covering realistic PDF/DOC/DOCX acceptance, MIME classifications, adversarial ZIP/PDF/OLE cases, scanner/storage non-persistence, clean upload/list/download, AAL2/ownership, and the scan-only boundary; 16 document UI tests passed.                                                                                                                                                                                                             |
| focused browser-completion suites                    | Passed: 5 web files/28 tests plus 52 focused API tests covering form/save/section behavior, automatic document states and safe categories, bounded portal access, public reflow source guards, exact admin application selection, lifecycle matrix, mismatch, history, audit, and candidate-visible request messages.                                                                                                                                                   |
| focused auth/provisioning suites                     | Passed: signed JWT verification, authoritative Auth-user confirmation, unmapped provisioning, access before/after provisioning, posting failures, rollback, idempotency, and existing authorization regression coverage; one explicit genuine-token case skipped without a supplied token.                                                                                                                                                                              |
| genuine local candidate journey                      | Passed: the focused Firefox case used Mailpit/PKCE, stable sign-in, real candidate TOTP/AAL2, actual file inputs, standard office-generated PDF and DOCX, real ClamAV/MinIO, success announcements/list refresh, safe fake-PDF/truncated-DOCX rejection, denied unauthenticated download/admin access, and factor cleanup. The earlier full run also passed posting-bound unmapped-identity recovery; the credential-gated assigned-onboarding fixture remains skipped. |
| genuine Firefox candidate stabilization              | Passed: three fresh closed-tab posting-bound sign-ins loaded the exact application without focus/visibility/resize/print/refresh assistance. The third run saved from the bottom action area with zero scroll delta, polite nearby **Draft saved**, and focus restored to the save button. The section outline remained nonsticky.                                                                                                                                      |
| genuine Firefox responsive matrix                    | Passed at 320, 375, 768, 1024, 1280, 1366, 1536, and 1920 CSS pixels at 100% zoom: complete hero, no loading fallback, no horizontal overflow, shared header/hero/trust outer alignment, bounded media, and intentional `58% 50%` hero focal position. 1280/1920 captures showed both subjects without right-edge crowding.                                                                                                                                             |
| `make build`                                         | Passed: Next.js 16.2.10 production build, including callback, sign-in-submit, MFA, candidate onboarding, admin onboarding, and proxy routes.                                                                                                                                                                                                                                                                                                                            |
| `make openapi` twice                                 | Passed and deterministic. `openapi.json`: `d4e114aa98b1faa1fc3fd546a2e94964be042db544f19eb4b68026c9999d6ece`; `generated.ts`: `9bd9a3c8f18472131e01781b13721fa61ab0bc7eaa68d6cf1d2f75716aefb17e`.                                                                                                                                                                                                                                                                       |
| changed-file formatting                              | Passed: edited Python was Ruff-formatted and edited web/tests/docs/contracts were Prettier-formatted.                                                                                                                                                                                                                                                                                                                                                                   |
| `alembic heads`                                      | Passed: single source head `20260717_0006`.                                                                                                                                                                                                                                                                                                                                                                                                                             |

The current local application database was already at source head. The required
read-only `docker compose run --rm api alembic current --check-heads` passed and
reported `20260717_0006 (head)`. The browser-stabilization pass added or edited
no migration; the existing remediation migration remains `0006`, and the
separate general Alembic-drift scope was not altered.

Migration validation used a separately named empty synthetic PostgreSQL
database. Full upgrade through `20260717_0006`, `current --check-heads`,
downgrade to `0005`, and re-upgrade to head all passed. The isolated database
was then removed. At head, `alembic check` returned exit 255 only for the known
general drift: candidate e-sign/information-request indexes, the historical
candidate-plan and programmatic-gate indexes, and historical task/policy
foreign-key `ondelete` metadata. No candidate-remediation column, constraint,
table, or index was reported missing.

With the corrected host-run local API running, `/health` returned service `ok`,
`/health/db` returned database `reachable`, and MinIO live health passed.
`verify_clamav.py --host 127.0.0.1 --port 3310` returned `clean: OK` and
`EICAR: FOUND`. Compose PostgreSQL, MinIO, and ClamAV were healthy;
`minio-init` completed successfully. The tracked Compose configuration and the
direct `docker compose config --quiet` check passed.

`apps/web/next-env.d.ts` remained byte-for-byte outside the diff after both
production builds.

The opt-in genuine local Supabase/Mailpit test ran with the repository's
browser-safe local anon key, published synthetic posting, and fresh disposable
identities. Both enabled cases passed; only the credential-gated
pre-assigned-onboarding fixture case skipped. The first enabled case additionally
proved stable pre-onboarding, valid draft save/submission, real candidate TOTP
AAL2, clean scan/object persistence, list refresh, and denied public/admin
access, then removed its synthetic factor. Repeated fresh runs preserved the
same-attempt idempotency boundary. No email, subject, UUID, token, cookie,
confirmation code, TOTP secret, QR URI, filename, private object key, or
provider payload was printed. The separate genuine-token verification case
still skips without `KEEPER_LOCAL_SUPABASE_ACCESS_TOKEN`; deterministic ES256
issuer/audience/expiry/signature/key/subject and authoritative-confirmation
tests passed.

The opt-in PostgreSQL concurrency proof was also run separately against a
second isolated empty database and passed. Its environment wrapper emitted two
shell-parse warnings for unquoted public display-name values in the existing
`.env`; it printed no values or secrets, did not edit `.env`, and did not affect
the passing test. That temporary database was removed.

## Residual risks

- The known general Phase 1D Alembic autogeneration drift remains separate.
- Legacy ambiguous review/onboarding rows require owner-approved reconciliation
  if they exist in retained data.
- Live Supabase/Mailpit callback and real admin AAL2 exercises now have local
  synthetic evidence. Refresh-token revocation/offboarding remains an
  operational exercise.
- The local-only admin identity link, corrected QR rendering, TOTP enrollment,
  AAL2 verification, and access to `/admin`, `/admin/candidates`, and
  `/admin/onboarding` have genuine local operator evidence.
- The corrected admin information-request selection/lifecycle path has full API
  and realistic component integration coverage, but a fresh genuine local admin
  browser send against the new synthetic submitted candidate was not performed:
  this session has no approved access to the operator's admin password/TOTP.
- Manual keyboard/screen-reader/cross-browser accessibility, host hardening,
  backup/restore, monitoring, retention, and operational access review remain
  readiness work. The required Firefox viewport matrix itself is complete.
- Final agent activation remains intentionally unimplemented.

## Review disposition

The focused candidate journey and complete command validation now pass. The
worktree is still not ready to commit or for final owner review because the
corrected information-request action has not received a fresh genuine admin
browser send with the existing linked AAL2 account. It is not pilot- or
release-ready: owner review, the separate
general Alembic-drift disposition, operational hardening, revocation exercises,
and release approval remain outstanding.

## Exact Git status

Branch `fix/candidate-auth-onboarding-completion` remains at starting HEAD
`f381dec4c08c2d50c452ed892fd60d9c7f287215`, tracking
`origin/fix/candidate-auth-onboarding-completion` at `0` ahead / `0` behind.
All remediation changes are unstaged; there are no staged changes.

```text
 M .env.example
 M AGENTS.md
 M Makefile
 M apps/api/src/keeper_api/api/routes/candidate_applications.py
 M apps/api/src/keeper_api/api/routes/candidate_documents.py
 M apps/api/src/keeper_api/api/routes/candidate_onboarding.py
 M apps/api/src/keeper_api/api/routes/recruitment.py
 M apps/api/src/keeper_api/api/routes/review.py
 M apps/api/src/keeper_api/api/routes/upload_document.py
 M apps/api/src/keeper_api/core/config.py
 M apps/api/src/keeper_api/models/domain.py
 M apps/api/src/keeper_api/schemas/candidate_applications.py
 M apps/api/src/keeper_api/schemas/review_onboarding.py
 M apps/api/src/keeper_api/services/auth.py
 M apps/api/src/keeper_api/services/candidate_applications.py
 M apps/api/src/keeper_api/services/candidate_files.py
 M apps/api/src/keeper_api/services/onboarding.py
 M apps/api/src/keeper_api/services/review.py
 M apps/api/tests/document_samples.py
 M apps/api/tests/test_authorization.py
 M apps/api/tests/test_candidate_applications.py
 M apps/api/tests/test_candidate_documents.py
 M apps/api/tests/test_compose_config.py
 M apps/api/tests/test_document_validation.py
 M apps/api/tests/test_integrations.py
 M apps/api/tests/test_openapi_contract.py
 M apps/api/tests/test_phase1d_review_onboarding.py
 M apps/api/tests/test_phase1e_migration.py
 M apps/web/app/(admin)/admin/candidates/candidate-review-pipeline.tsx
 M apps/web/app/(admin)/admin/onboarding/onboarding-admin.tsx
 M apps/web/app/(admin)/layout.tsx
 M apps/web/app/(candidate)/candidate/applications/[applicationId]/application-form.tsx
 M apps/web/app/(candidate)/candidate/applications/[applicationId]/candidate-documents.tsx
 M apps/web/app/(candidate)/candidate/onboarding/candidate-onboarding-dashboard.tsx
 M apps/web/app/(candidate)/candidate/onboarding/page.tsx
 M apps/web/app/(candidate)/layout.tsx
 M apps/web/app/(public)/careers/[slug]/page.tsx
 D apps/web/app/(public)/loading.tsx
 M apps/web/app/auth/callback/route.ts
 M apps/web/app/auth/register/page.tsx
 M apps/web/app/auth/sign-in/page.tsx
 M apps/web/app/auth/sign-in/sign-in-form.tsx
 M apps/web/app/globals.css
 D apps/web/app/loading.tsx
 M apps/web/lib/candidate-browser-api.ts
 M apps/web/lib/candidate-provisioning.ts
 M apps/web/lib/portal-access.ts
 M apps/web/lib/portal-server-api.ts
 M apps/web/lib/require-portal-access.ts
 M apps/web/lib/review-onboarding-api.ts
 M apps/web/lib/routes.ts
 M apps/web/package.json
 M apps/web/tests/candidate-application-ui.test.tsx
 M apps/web/tests/candidate-documents-ui.test.tsx
 M apps/web/tests/candidate-registration.test.tsx
 M apps/web/tests/portal-access.test.ts
 M apps/web/tests/public-source-safety.test.ts
 M apps/web/tests/recruitment-workflows.test.tsx
 M compose.yaml
 M docs/05_DOMAIN_MODEL_AND_LIFECYCLES.md
 M docs/06_UX_UI_IMPLEMENTATION_GUIDE.md
 M docs/08_ACCEPTANCE_TESTS.md
 M docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md
 M docs/11_ENVIRONMENT_VARIABLES.md
 M docs/12_THREAT_MODEL.md
 M docs/13_API_AND_DATA_INVENTORY.md
 M docs/14_TEST_STRATEGY.md
 M docs/15_KNOWN_LIMITATIONS.md
 M docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md
 M docs/21_LINUX_MINT_CONTINUATION_READINESS_REPORT.md
 M docs/22_CANDIDATE_AUTH_AND_ONBOARDING_READINESS_ASSESSMENT.md
 M docs/LOCAL_DEVELOPMENT.md
 M packages/contracts/openapi.json
 M packages/contracts/src/generated.ts
?? apps/api/alembic/versions/20260717_0006_candidate_auth_onboarding_completion.py
?? apps/api/scripts/link_local_admin_identity.py
?? apps/api/scripts/run_local_api.py
?? apps/api/tests/test_candidate_remediation_migration.py
?? apps/api/tests/test_link_local_admin_identity.py
?? apps/api/tests/test_supabase_jwt_verification.py
?? apps/web/app/auth/mfa/
?? apps/web/app/auth/sign-in/submit/
?? apps/web/lib/mfa-return.ts
?? apps/web/proxy.ts
?? apps/web/tests/admin-information-request.test.tsx
?? apps/web/tests/admin-mfa.test.tsx
?? apps/web/tests/candidate-mfa.test.tsx
?? apps/web/tests/candidate-sign-in.test.tsx
?? apps/web/tests/local-candidate-auth-journey.integration.test.ts
?? apps/web/tests/onboarding-navigation.test.tsx
?? apps/web/tests/supabase-session-refresh.test.ts
?? docs/23_CANDIDATE_AUTH_ONBOARDING_COMPLETION_IMPLEMENTATION_REPORT.md
```

`apps/web/next-env.d.ts`, `.env`, issued historical migrations, and historical
Phase 1C/1D implementation reports are absent from the diff.
