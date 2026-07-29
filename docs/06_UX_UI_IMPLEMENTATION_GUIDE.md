# UX/UI Implementation Guide

## Design source

Three owner-approved 1122 × 1402 desktop mockups are stored in `docs/ui/reference`: home, recruitment, and agent profile.

Treat the mockup as the primary visual reference for:

- Brand tone.
- Typography direction.
- Spacing.
- Navigation.
- Cards.
- Forms.
- Buttons.
- Image treatment.
- Public-site composition.

Do not copy inaccessible interactions or layouts without adaptation.

## Phase 1A translation

- Shared tokens use the approved paper, ink, warm gold, fine-border, restrained-shadow, editorial-serif, and sans-serif direction.
- Public heroes use a split copy/image composition on wide screens and a single-column crop-safe layout on narrow screens.
- The public header exposes all approved navigation labels in a desktop navigation and a keyboard-native `details`/`summary` mobile menu.
- Service cards, process steps, dark calls to action, empty states, policy content, and recruitment sections are reusable patterns rather than screenshot-specific markup.
- The logo is a semantic text/CSS lockup. The owner approved this treatment for production use on 2026-07-29; a standalone vector logo is not required for the recruitment refresh.
- Two photography-only raster assets were generated from the approved home and recruitment mockups as visual references. They contain no embedded UI, brand text, rates, awards, testimonials, or sample data and are documented in `docs/ui/README.md`.
- The agent-profile mockup informed card, border, icon, and spacing treatment only. No CRM dashboard, client, application, production, pipeline, appointment, or portal feature was implemented in Phase 1A.

## Product experience principles

- Premium but not ornamental.
- Local and trustworthy.
- Clear regulatory identity.
- Plain language.
- Strong mobile experience.
- One primary action per section.
- Avoid unnecessary financial jargon.
- Separate marketing pages from secure workflows.
- Always show system status after user actions.
- Never rely on color alone.

## Public navigation

Recommended:

- Mortgages
- How it works
- Our agents
- Join Keeper Financial
- About
- Contact
- Get started

## `/apply` page

The page must present both options without making either look secondary.

### Speak with someone first

- Short explanation.
- Minimal form.
- Call action.
- Consultation-booking action.
- Expected response language.
- Privacy acknowledgement.

### Start a secure application

- Enter the exact Keeper-owned `apply.keeperfinancial.ca` workflow; do not redirect to an external provider.
- State expected time only where verified.
- Explain that the accountless draft resumes only in the same browser while its secure capability remains valid; do not imply emailed or cross-device resume.
- Use a direct call to action with adjacent privacy/security guidance.
- Keep the full application separate from the minimal contact form rather than duplicating sensitive fields on `/apply`.
- The borrower workflow must provide accessible step navigation, explicit required/optional labels, linked error summaries, save state, review before submission, document status, consent immediately before submission, and no sensitive browser persistence.

## Candidate portal

As implemented by the 2026-07-17 remediation, the published-posting page,
registration page, posting-bound sign-in page, confirmation callback, and
bounded recovery errors retain only a server-validated published slug.
Candidate onboarding appears in portal navigation only after the protected
dashboard proves a current eligible assignment.

- Every published posting must present two equally clear candidate entry actions: create an account and sign in with an existing account. Both actions must preserve the validated posting slug through authentication and return to that posting-specific application start.
- Registration confirmation and existing-user sign-in must converge on a supported posting-bound provisioning orchestration that invokes the narrow application-start boundary. Generic sign-in remains non-provisioning and must not infer a posting or grant candidate access.
- If a user is already confirmed in Supabase but has no local mapping/application relationship, the posting-bound entry flow must explain the denial safely and offer recovery by returning to a published posting and signing in with that preserved posting context. It must not create a candidate relationship without an explicit published-posting start.
- Authentication errors must retain safe posting context, avoid account-enumeration detail, and provide a visible route back to the selected opportunity.
- A section outline in normal document flow; it must not be sticky
  noninteractive text that obscures form content.
- Draft-save status both at the workflow level and beside the action. The
  action-local polite live region distinguishes saving, saved, validation,
  network, and stale-revision states without scrolling the candidate away from
  the controls.
- Clear required/optional labels.
- Review screen before submission.
- Candidate-visible messages separate from internal notes.
- Status timeline.
- Task-oriented onboarding dashboard.
- Document version and completion state.
- Candidate portal navigation must expose onboarding when an onboarding assignment is available; the direct route must remain authorization- and lifecycle-protected even when the navigation item is absent or ineligible.

## Public recruitment journey

The owner-approved 2026-07-29 recruitment direction makes `/careers` the main public entry point for mortgage-agent recruitment while preserving the posting-specific candidate boundary.

- Lead with the Ontario mortgage-agent audience, competitive compensation, more earning potential, autonomy, available lead opportunities, coaching, mentorship, dedicated brokerage support, and broad lender access.
- Do not publish CRM, marketing-automation, or document-management claims; awards, rankings, “best” or “leading” comparisons; testimonials that do not yet exist; agent earnings or growth statistics; or invented compensation details, lead volumes, lender counts, or timelines.
- When exactly one posting is published, link the hero, featured opportunity, and closing action to that posting's detail page. Do not bypass role review by linking `/careers` directly to registration.
- Preserve honest zero-posting and API-unavailable states. If more than one posting is returned, show every published posting rather than silently selecting one.
- Keep the brokerage story visible when no posting can be shown, but do not add a general-interest form, résumé inbox, newsletter, or new candidate-data path.
- Explain the implemented journey factually: review the role without an account, create a posting-specific application and save a draft, follow candidate-visible updates, and complete controlled onboarding only if selected.
- The existing recruitment image is approved for use. Its alternative text and surrounding copy must not present the generated scene as real Keeper employees, premises, or a testimonial.

## Admin portal

As implemented by the 2026-07-17 remediation, the authorized admin shell
exposes onboarding administration. Review controls display and submit the
posting-specific application ID and attempt; navigation remains a convenience
over the FastAPI authorization boundary.

- Queue first.
- Filters by status, owner, age, and missing requirements.
- Candidate detail organized into application, documents, review, onboarding, activity.
- Administration navigation must expose onboarding plan/assignment/task/gate operations to authorized administrators.
- Clear destructive-action confirmation.
- Reason required for high-risk status changes.
- No hidden status changes.

## Agent profiles

Standard fields:

- approved photo;
- licensed name;
- approved title;
- licence number;
- languages;
- service areas;
- specialties;
- biography;
- approved contact details;
- approved social links;
- application/contact attribution;
- brokerage identity.

## Component baseline

Create:

- App shell.
- Public header/footer.
- Portal side navigation.
- Page header.
- Card.
- Form field.
- Error summary.
- Button variants.
- Status badge.
- Data table.
- Timeline.
- Progress checklist.
- Empty state.
- Loading state.
- Error state.
- Confirmation dialog.
- File-upload control.
- Consent checkbox.
- Breadcrumbs.

## Responsive requirements

- Public pages must work from small mobile through desktop.
- Admin tables may switch to cards on narrow screens.
- No horizontal page scrolling at 320 CSS pixels.
- Touch targets should be practical.
- Portal navigation must remain usable without hover.

Implemented public reflow guardrails include page-level overflow clipping,
`min-width: 0` on layout containers, one centered max-width geometry shared by
the header, hero, trust strip, and following sections, single-column layouts
below 52rem, full-width actions on the smallest breakpoint, intentional
crop-safe `next/image` sizing/focal positioning, and explicit 36rem
narrow-screen rules. Genuine Firefox evidence at 320, 375, 768, 1024, 1280,
1366, 1536, and 1920 CSS pixels showed no horizontal overflow at 100% zoom;
broader manual WCAG and cross-browser approval remain Phase 1F work.

## 2026-07-18 candidate browser-completion addendum

- The shared candidate shell uses the bounded onboarding-availability projection, not the full protected dashboard. No assignment hides the navigation item and leaves the application portal usable; permanent denials are not polled, and a transient direct-dashboard failure offers one manual retry.
- Candidate application fields expose the Phase 1C format, length, optionality, and conditional rules before submission. Month values use an accessible month control with canonical `YYYY-MM`; referral detail is rendered and submitted only for employee/agent referral or Other; the interest statement announces its 100-character minimum and current count.
- Safe API validation failures produce an announced summary linked to affected controls without clearing entered values or displaying internal schema paths.
- The candidate document area inspects MFA before requesting private metadata. It offers enrollment without a verified factor, challenge at AAL1 with a verified factor, and returns only to an allow-listed exact candidate application `#documents` location after session refresh proves AAL2.
- After AAL2, private document metadata loads automatically and resolves to a
  list, explicit empty state, or bounded retry. Upload feedback distinguishes
  unsupported extension, declared/detected MIME disagreement, PDF/DOC/DOCX
  structural rejection, file size, malware, scanner availability, storage
  availability, and authorization without exposing parser or storage details;
  a successful upload resets only the file control, preserves category, and
  refreshes the visible metadata.
- Information-request, interview, decision, and onboarding controls retain the exact selected opportunity and attempt. Information request remains disabled until the selected attempt is `under_review` or `interview`, and conflicts use operation-specific wording.
