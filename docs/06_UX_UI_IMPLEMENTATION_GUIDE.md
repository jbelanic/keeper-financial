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
- The logo is a semantic text/CSS lockup because no approved standalone vector logo was supplied.
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

- Explain that financial information will be entered in the selected secure mortgage platform.
- State expected time where verified.
- Explain save-and-return only when supported by the vendor.
- Direct call to action.
- No embedded duplicate application form.

## Candidate portal

- Persistent progress indicator.
- Save status.
- Clear required/optional labels.
- Review screen before submission.
- Candidate-visible messages separate from internal notes.
- Status timeline.
- Task-oriented onboarding dashboard.
- Document version and completion state.

## Admin portal

- Queue first.
- Filters by status, owner, age, and missing requirements.
- Candidate detail organized into application, documents, review, onboarding, activity.
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

Implemented public reflow guardrails include page-level overflow clipping, `min-width: 0` on layout containers, single-column layouts below 52rem, full-width actions on the smallest breakpoint, crop-safe `next/image` containers, and explicit 36rem narrow-screen rules. Browser/manual WCAG and visual-regression approval remain Phase 1F work.
