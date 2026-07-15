# Acceptance Tests

## Public and SEO

- Public pages render without authentication.
- Public pages have unique titles and descriptions.
- Sitemap excludes private routes.
- Robots excludes candidate, admin, and authentication areas.
- Public header and footer contain the approved navigation destinations.
- Canonical and Open Graph metadata use validated site configuration.
- Owner-supplied public name, regulatory text, address, email, phone, and application destination match controlled configuration.
- Missing optional booking/principal-broker values remain disabled or absent rather than becoming claims.
- Draft/suspended/archived agent profiles return non-public behavior.
- Closed recruitment postings are not listed publicly.
- Mobile layout remains usable at 320 CSS pixels.
- Public navigation uses keyboard-native controls and all public actions remain real links or native controls.
- Mockup-only people, ratings, lender counts, rates, licence examples, testimonials, and portal metrics do not appear in public source.

Phase 1A public-site evidence remains in `docs/17_PHASE_1A_IMPLEMENTATION_REPORT.md`. Phase 1B adds focused apply-form, attribution, booking, protected lead-queue, no-store request, consent-state, pagination, withdrawal-confirmation, and route-protection coverage.

## Apply flow

- `/apply` shows both paths.
- Contact-first form submits approved minimal fields.
- Consent wording/privacy versions and source/capture source are selected only by the server; caller override fields are rejected as extras.
- Required service-contact acknowledgement is enforced.
- Marketing consent remains optional and unchecked by default.
- A marketing-consent record is created only when selected.
- Prominent and adjacent free-text warnings cover financial, identity, health, credential, and underwriting information.
- Overly long, sensitive, control-character, unknown, and automation-trap input is rejected.
- Valid query attribution becomes a hidden controlled slug; invalid attribution is omitted and unpublished/unknown profiles are rejected by the API.
- Pending submission disables duplicates; errors preserve values, focus an announced summary, and map `422`, `429`/`Retry-After`, `503`, server, and network failures without exposing internals.
- Success is announced and is the only state that resets the form.
- Full application redirects only to configured HTTPS allowed hosts.
- Agent redirect attribution uses only safe grammar and an approved configuration mapping.
- No sensitive information appears in redirect URL.
- Phone remains a real `tel:` action; book-a-call renders only for a validated optional HTTPS URL.

## Lead administration

- `GET /api/v1/leads` and marketing withdrawal deny anonymous, unmapped identity, mapped identity-only, inactive, wrong-role, candidate, and admin-without-required-MFA callers; an active verified AAL2 admin is allowed.
- The list is no-store, maximum 100 rows per request, offset-paginated, newest-first by `created_at` then `id`, and accepts only lifecycle status filtering.
- Queue URLs contain only safe page/status values; list output contains the necessary lead fields and explicit service/marketing consent states and timestamps.
- Withdrawal affects only the lead’s marketing consent, preserves `granted_at`, sets `withdrawn_at` once, is idempotent, and never changes service acknowledgement.
- First withdrawal creates exactly one `marketing_consent.withdrawn` audit with actor, request ID, target consent ID, and safe capture source. Unknown lead or absent marketing consent returns a safe `404`.
- Lead, service consent, optional marketing consent, and audits roll back together on persistence failure.
- Request logs and audit metadata exclude contact fields, message, tokens, raw payloads, and private URL/query values.

## Authentication and authorization

- Anonymous user cannot access candidate or admin routes.
- Authenticated identity without local application access is denied.
- Candidate can access only own record and documents.
- Candidate cannot access internal notes.
- Candidate cannot access another candidate by changing an identifier.
- Admin action requires correct role.
- Suspended/offboarded account is denied.
- Role revocation takes effect.

## Candidate application

- Candidate saves draft.
- Required fields prevent submission.
- Submission creates status history and audit event.
- Submitted application cannot be silently edited.
- Information request reopens only approved sections or creates a controlled response path.
- Withdrawal follows valid transition policy.

## Review

- Invalid status transitions fail.
- Decline requires reason.
- Suspension requires reason.
- Status history is append-only through normal application operations.
- Candidate-visible message is separate from internal note.

## Documents

- Upload rejects unsupported file types and excessive size.
- Private object cannot be fetched anonymously.
- Authorized retrieval is short-lived or proxied.
- Candidate cannot retrieve another candidate’s file.
- Issued document version cannot be edited.
- New revision supersedes prior version.
- Acknowledgement references exact version.
- Acceptance/rejection creates audit evidence.

## Onboarding

- Plan can be assigned only to eligible candidate state.
- Mandatory tasks prevent activation.
- Override requires authorized role and reason.
- FSRA verification is recorded as administrative evidence, not asserted automatically.
- System provisioning task can be completed manually.
- Activation creates audit evidence.

## Agent profiles

- Draft is private.
- Candidate or agent cannot self-publish.
- Approval is required.
- Suspended profile is removed from public directory and direct public rendering.
- Published page contains configured regulatory fields.
- Agent-specific application path uses configured safe mapping.

## Environment and operations

- Nonlocal startup fails with local storage.
- Nonlocal startup fails with development auth.
- Nonlocal startup fails with wildcard CORS.
- Health endpoint works without exposing secrets.
- Database health distinguishes API health from database connectivity.
- Logs do not contain tokens or raw document URLs.
