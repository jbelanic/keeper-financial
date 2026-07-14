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

Phase 1A web evidence: 9 Vitest files / 27 tests cover anonymous page rendering, metadata uniqueness, sitemap, robots, shell navigation/contact facts, configuration fail-closed behavior, dynamic publication boundaries, source claim leakage, reflow guardrails, apply privacy copy, and portal API requests. The production Next build prerenders 30 pages/routes without metadata, routing, hydration, or type errors.

## Apply flow

- `/apply` shows both paths.
- Contact-first form submits approved minimal fields.
- Required service-contact acknowledgement is enforced.
- Marketing consent remains optional.
- A marketing-consent record is created only when selected.
- Free-text warning is visible.
- Overly long and disallowed input is rejected.
- Full application redirects only to configured HTTPS allowed hosts.
- Agent attribution uses an allowed agent identifier.
- No sensitive information appears in redirect URL.

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
