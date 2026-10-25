# Keeper Financial — Public-Facing Copy Review (Before / After Change List)

| | |
|---|---|
| **Prepared** | 2026-10-16 |
| **Prepared by** | keeper-architect |
| **Scope** | Public marketing + institutional pages: `/`, `/mortgages`, `/mortgages/[slug]`, `/broker`, `/how-it-works`, `/apply`, `/contact`, `/agents`, `/agents/[slug]`, `/about`, `/careers`, `/careers/[slug]`, `/privacy-policy`, `/complaints`, `/accessibility`, plus the shared public shell (header/footer) and the accountless borrower application surface |
| **Excluded** | Candidate/agent/admin portals (internal), email templates, API error contracts, the owner-approved borrower consent wording text |
| **Method** | Read every public page/component on the current checkout, cross-checked against a live capture of `https://keeperfinancial.ca` (all strings below are the **rendered** strings, not just source) |
| **Evidence base** | Repo `feat/ops-minio-restore` @ `44ce7ec` (copy files unchanged from `origin/main`); live capture of 12 public URLs on 2026-10-16 |
| **Status** | **Approved and implemented** on 2026-10-16 (owner + legal, decision 50). Branch `content/public-copy-review`; see §0 for the implementation record, exceptions and verification |

## 0. Implementation record

**Approved and implemented on 2026-10-16** (owner + legal review; decision 50 in
`docs/09`). Branch `content/public-copy-review`, three commits on top of
`origin/main` @ `97fef2b`:

| Commit | Contents |
| --- | --- |
| `0fdd421` | `feat(web): revise public copy to the approved plain-language standard` |
| `a742c39` | `docs: record the public copy review decision and sync living documents` |
| `015db42` | `fix(web): keep a valid heading order on the agent list` |

Twenty-nine files: 24 under `apps/web` (every `app/(public)` page, `lib/public-content.ts`,
`lib/public-components.tsx`, `lib/shells.tsx`, `app/layout.tsx`, `app/globals.css`, and 3
test files) and 5 living documents (`docs/00`, `docs/06`, `docs/09`, `docs/15`, `docs/26`).

Everything from §1 onward is the change list **as written before implementation**. The
exceptions, deviations and additions below are where the delivered work differs from it.

> **Dated note — 2026-10-25 (decision 55).** Part of this record is no longer current.
> The home-page hero description, both hero CTA labels and destinations, the closing CTA
> band copy, and the `/apply` page framing recorded here were replaced by the homepage
> conversion update, which also makes `/apply` the mortgage readiness review surface.
> Every other approved string in this review — including all required disclosures — is
> still in force. See decision 55 in `docs/09` for the current copy. This document stays
> as the record of the 2026-10-16 review.

### Not changed, with reasons

| Item | Reason |
| --- | --- |
| C-15 — move "Agent sign in" | Footer utility placement was not part of the approved change. Left as-is. |
| C-16 — nav label "Our agents" | Owner directed that the "Find an Agent" label and nav item stay (an agent profile is publishing shortly). |
| C-60 — `brokerSummary` eyebrow | Approved `/broker` copy; changing its eyebrow would collide with the broker page's own eyebrow. Unchanged. |
| C-68 / C-69 — consent and marketing statements | Consent wording is not reworded casually; both were already clear and accurate. Unchanged. |
| C-104 — article titling | The apparent "Privacy Notice" duplication is the breadcrumb plus the `h1` — standard on every interior page. No action needed. |
| C-105 — typed-data restructure of the notice | Refactoring approved legal-text rendering has no user-visible benefit and carries real risk. Deliberately deferred. |

### Deviations from the list

- **C-10** — the unreachable 503 branch was kept but reworded rather than deleted. The lead
  endpoint never returns 503, but an ingress/proxy 503 for that POST is plausible, so the
  message is now product-neutral ("We couldn't send your request right now. Nothing was
  submitted…").
- **Agent card heading order** — removing the visible "Agent directory" heading left the
  cards as `h3` directly under the `h1`. Promoting card names to `h2` would have jumped the
  card type from 1.28rem to ~2.6rem, so the section carries a visually-hidden `h2` and is
  labelled by it instead (`015db42`).
- **Layout trap** — the removed heading was the first column of a two-column
  `container reading-layout` grid. Deleting it alone would have crushed the agent cards into
  the narrow column, so the container is now full width — which also delivers the requested
  extra real estate and reduces scroll.
- **Two extra edits not in the list** — the `careers/[slug]` noindex fallback metadata was
  reworded to match its `agents/[slug]` equivalent (C-40), and the `/contact` metadata
  description was tightened so no "published" vocabulary remains in public metadata.

### Corrections made while implementing

- The proposed home heading "Three steps, no runaround" was wrong: the section renders
  **four** steps. It ships as "A simple path to your mortgage".
- The Privacy Notice hardcoded the old effective date in the page-header prop as well as in
  the notice body. Both now read 2026-10-16.

### Verification (branch state as committed)

```
npx prettier --check app lib tests *.ts *.mjs   All matched files use Prettier code style!
npm run lint                                    clean, 0 warnings
npm run typecheck                               clean
npm test                                        195 passed | 3 skipped (37 files passed, 1 skipped)
npm run build                                   ✓ Compiled successfully
pytest apps/api/tests  (BORROWER_APPLICATION_ENABLED=false)   650 collected, exit 0
ruff check apps/api   /   mypy apps/api/src     All checks passed! / Success: 70 source files
```

Rendered-output verification served the built app and read all 11 prerendered pages plus
`/agents`, `/apply` and `/careers`: no "Agent directory", no "Published profile", no hero
subheading on the agent page, and the Privacy Notice renders the new section as a heading
with no authoring instructions and no Filogix statement.

### Still requires a human read-back before public deployment

1. The Privacy Notice paragraphs **authored during implementation** from `docs/28` and the
   Phase B/C/D field inventory: "Through the mortgage application, we collect…", the
   *Retention* sentence (seven years / 30 days of inactivity, per decision 37), the
   *Safeguards* encryption-and-authorized-access sentence, and the *Mortgage applications
   and credit review* section.
2. The displayed registration text `FSCO # 13696` — FSCO has been replaced by FSRA. Flagged
   in `docs/09` assumptions and in decision 50; deliberately not self-corrected.
3. Anonymous-reachable auth surfaces (`/auth/sign-in`, `/auth/register`) and the candidate
   portal still use "currently published opportunity" wording. Same vocabulary class, but
   outside the approved scope of this review — recommended as a small follow-up.


**Severity legend**

- **P0** — Published content that is wrong, misleading, internal-only, or contradicts an approved boundary. Fix before any further public polish.
- **P1** — Public-facing language that reads technical, procedural, or institutional; strongest impact on perceived professionalism.
- **P2** — Polish: consistency, duplication, sentence style.

**Sign-off legend**

- **[owner]** — owner decision needed (product/positioning).
- **[legal]** — compliance/regulatory/claims review needed; do not let a dev agent freelance this.
- **[safe]** — mechanically safe copy edit; no claim, disclosure, or behaviour change.

---

## 1. Summary of findings

The copy has three systemic problems, not just scattered awkward lines.

**A. Internal/production vocabulary is published verbatim.** Words that describe *how the system was built* — **published / publication** ("Published profile", "Agent directory", "Published identity", "Published roles", "Browse currently published profiles"), **configured / validated** ("configured mortgage application service", "validated route"), **authorized secure process**, **information minimization**, **secure handoff**, **non-sensitive context**, **real contact route** — appear on almost every page. To a visitor these read as machine-generated and slightly evasive. They are the single biggest reason the site does not feel like a professional brokerage website.

**B. The same idea is repeated 2–4 times per page, and one page repeats an instruction to the author.** The home page's trust strip chains sentences (`Clear information` → next item's bold label is `General questions first` → next item is `Sensitive details stay in the application`), the home "contact a specific agent" block renders the **same sentence twice as heading and paragraph**, the home "How it works" description duplicates the four numbered steps directly beneath it, and mortgage detail pages state the "general info here / details in the application" boundary **three times** in one screen. The privacy notice and accessibility page go further and publish **"before publication, insert…" authoring instructions** and internal release-planning notes to the public.

**C. The pages carry process and policy, but almost no brokerage value messaging.** The home page — the one page an Ontario borrower sees first — says nothing about who Keeper is, what borrowers get, or why to choose Keeper over a bank. The most persuasive approved copy (multiple lenders, licensed professionals, local Ontario guidance) lives only on `/broker` and `/mortgages/*`. Meanwhile the home page spends its prime real estate on data-boundary housekeeping that is already explained at the point of contact.

Two further pages contain **substantive defects** rather than tone problems: the privacy notice says a complete application "is handled through Filogix" (the approved MVP has **no Filogix integration** — decisions 3/38, `docs/28`), and the `/apply` page states "Final submission and document upload are not yet available" although both are implemented (`docs/34`, Phase D.2) .

---

## 2. P0 — fix first

### P0-1 · Privacy Notice publishes authoring instructions

`apps/web/app/(public)/privacy-policy/page.tsx` (`APPROVED_CONTENT`, lines 5–58)

| # | Current (live) | Proposed | Sign-off |
|---|---|---|---|
| C-01 | Under *Service providers and disclosure*: **"Before publication, Keeper Financial must confirm the approved provider categories, subprocessors, processing locations and contractual safeguards."** | **"We use vetted service providers for hosting, storage, security, monitoring and communications. They may process personal information only on our instructions and only as needed to provide those services."** | [legal] |
| C-02 | Under *Retention*: **"Before publication, insert approved retention principles or link to the approved schedule. Do not insert fixed periods or legal-hold wording until approved by legal and privacy reviewers."** | Replace with an approved retention statement (decision 37 authorises seven-year submitted-record retention and 30-day drafts) or delete the block entirely if legal prefers to defer. **Do not invent periods.** | [legal] [owner] |
| C-03 | Under *Cookies*: "If non-essential technologies are introduced, this notice and any required choices must be updated before deployment." | "If we introduce analytics, advertising or preference cookies, we will update this notice and provide any choices required by law before they are used." | [legal] |
| C-04 | Effective date "Jul 23, 2026" | Update to the date these corrections publish, and record the change in `docs/09`. | [legal] |

> These three sentences are internal review instructions that leaked into public copy. They are the most visible credibility problem on the site.

### P0-2 · Privacy Notice names a vendor the product does not use

| # | Current (live) | Proposed | Sign-off |
|---|---|---|---|
| C-05 | Section *Mortgage applications and external services*: **"A complete mortgage application is handled through Filogix. When you follow an external link, the destination's privacy terms and security practices may also apply. Review those materials before submitting detailed information."** | Describe the **Keeper application** as the intake channel: the information collected (personal details, SIN, income/employment, assets, liabilities, subject and other properties, supporting documents), that it is stored in Keeper's private encrypted storage, and that it is reviewed by the assigned licensed agent / administrators. Retain the external-link sentence only if the notice links out elsewhere. | [legal] [owner] |

**Why this is P0:** the MVP explicitly has no Filogix redirect, handoff, export, or API integration (`docs/00` L32/L41, `docs/28` L24, decisions 3 and 38). The current sentence misdescribes where a borrower's data goes — a privacy-accuracy defect, not a wording preference.

### P0-3 · The Privacy Notice does not cover the borrower application at all

The notice describes data collected through (a) the public contact form and (b) the candidate portal. Keeper is now the approved **system of record for borrower mortgage applications** (`docs/28`) including SIN, financial data, and supporting documents, with a versioned privacy/credit-use consent. The public notice must disclose that class of collection, use, retention and disclosure.

| # | Change | Sign-off |
|---|---|---|
| C-06 | Add a *Mortgage application* section covering: what is collected, the purpose (assessing and submitting a mortgage application), who can see it (assigned licensed agent, authorised administrators), where it is stored, the credit-use consent, retention, and access/correction requests. | [legal] [owner] |

### P0-4 · Accessibility page publishes internal release-planning text

`apps/web/app/(public)/accessibility/page.tsx` L122–127

| # | Current (live) | Proposed | Sign-off |
|---|---|---|---|
| C-07 | **"The accessibility statement on this page is approved site content. A separate formal specialist accessibility review remains a deferred production-readiness item, but accessibility is incorporated into the site and is not a standalone release blocker."** | **Delete the paragraph entirely.** (If a review-status sentence is required, it must be an approved public commitment, not a sprint note.) | [legal] |
| C-08 | "Keeper Financial's website implementation includes automated checks and behaviour-focused accessibility review during development." | "We test accessibility as we build, and we treat accessibility barriers as defects that get prioritised and fixed." | [safe] |

### P0-5 · `/apply` states a capability limitation that no longer exists

`apps/web/app/(public)/apply/apply-paths.tsx` L74–81

| # | Current (live) | Proposed | Sign-off |
|---|---|---|---|
| C-09 | "…**Final submission and document upload are not yet available.** If the application is unavailable, call +1 (709) 700-7339 or email support@keeperfinancial.ca." | Remove the stale sentence; keep the browser/draft guidance: *"Your draft is saved as you go and resumes only in this browser, so please don't use a shared or public device. If the application isn't available, call or email us and we'll help you directly."* | [owner] |

**Important caveat:** submission and document upload are implemented (`docs/34`, migration `20260726_0015`), but real-data submission is currently **fail-closed in production** until `BORROWER_REAL_DATA_ENABLED=true` and the consent row is marked `real_data_approved`. So today's sentence is *operationally* true but *source*-false. Owner decides which statement to publish:

- **(a)** remove it (recommended once real-data submission is enabled), or
- **(b)** replace with an accurate non-technical disclosure while the gate is on, e.g. *"We're onboarding applications in stages. You can start and save your application now, and we'll confirm the next step with you."*

Do not simply delete and leave a page that promises a submission the live environment refuses.

### P0-6 · Contact form shows the wrong error for an impossible status

`apps/web/app/(public)/apply/apply-form.tsx` L129–132

| # | Current | Proposed | Sign-off |
|---|---|---|---|
| C-10 | `503` branch: "**The mortgage application is temporarily unavailable.** No application information has been submitted…" | The lead endpoint returns 201/422/429/500 only (`apps/api/src/keeper_api/api/routes/leads.py`) — the 503 branch is unreachable and names the wrong product. Either delete the branch or reword the generic 5xx message to: *"We couldn't send your request right now. Nothing was submitted — please try again in a moment, or call or email us."* | [safe] |
| C-11 | `unavailableContact` default (L58): "the published phone or email contact" | "our phone number or email address" | [safe] |

### P0-7 · `<title>` on `/careers` duplicates the brand

`apps/web/app/(public)/careers/page.tsx` L15 · root template is `"%s | Keeper Financial"` (`app/layout.tsx` L10)

| # | Current (live) | Proposed | Sign-off |
|---|---|---|---|
| C-12 | `Ontario Mortgage Agent Careers \| Keeper Financial \| Keeper Financial` | `title: "Ontario Mortgage Agent Careers"` (template appends the brand once) | [safe] |

### P0-8 · Footer renders a double period

`apps/web/lib/shells.tsx` L167–170 — `legalName` = "Keeper Financial Inc." then `"."`

| # | Current (live) | Proposed | Sign-off |
|---|---|---|---|
| C-13 | `© 2026 Keeper Financial Inc.. All rights reserved.` | `© {year} {siteConfig.legalName} All rights reserved.` (drop the concatenated period) | [safe] |

---

## 3. Site-wide vocabulary — translate, then rewrite

Apply this everywhere before touching individual pages. This alone removes most of the "technical" feel.

| Internal / procedural phrasing (current) | Public phrasing (proposed) |
|---|---|
| published profile · published opportunity · currently published · no longer published | *(delete)* → "our agents" · "open roles" · "current openings" |
| published identity · published public contacts | "Brokerage information" · "Contact us" |
| the configured mortgage application service | our secure application |
| through a validated route | *(delete)* |
| an authorized secure process · another authorized secure channel | our secure application · our encrypted application |
| non-sensitive context · non-sensitive message | a short note about what you need |
| general contact channels | email or phone |
| data minimization · information minimization | Your privacy |
| secure handoff | Security by design |
| a real contact route | *(delete)* → "Call, email, or use the form" |
| Please try again later or contact Keeper Financial | Please try again shortly, or call or email us |
| Contact Keeper Financial *(3rd-person self-reference, used 20+ times)* | Contact us · Talk to us · We'll help |
| Agent directory | Keeper Financial agents *(or delete the heading)* |
| Agent-specific application attribution is managed through… | *(delete)* |

---

## 4. Page-by-page before / after

### 4.1 Shared shell (header / footer)

`apps/web/lib/shells.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-14 | 86–89 | "Plain-language mortgage information and a secure way to take the next step." | "Clear mortgage guidance and a secure way to apply — from a licensed Ontario brokerage." | [owner] |
| C-15 | 175–177 | "Agent sign in" | "Agent sign in" *(keep)* — but consider moving it out of the public footer's disclosure zone into a small utility line. | [owner] |
| C-16 | 1–8 (`lib/public-content.ts`) | Nav: "Find an Agent" | "Our agents" (`docs/06` L50 already recommends this). Optional but more natural for a public nav. | [owner] |
| C-17 | `app/layout.tsx` 11–13 | "Plain-language mortgage guidance and secure next steps from Keeper Financial in Ontario." | "Keeper Financial is a licensed Ontario mortgage brokerage helping borrowers compare options and apply securely online." | [owner] |

**Do not touch:** the FSCO regulatory line, "Mortgage options are subject to borrower qualification and lender approval", the privacy/complaints/accessibility footer links.

### 4.2 Home page — `app/(public)/page.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-18 | 49–70 | **Trust strip = three chained duplicates.** `Clear information / General questions first` → `General questions first / Sensitive details stay in the application` → `Sensitive details stay in the application / Keep detailed information in the mortgage application` | Replace with **three independent value statements** (each bold label ≠ next body): <br>**`Licensed Ontario brokers`** — *"Talk to licensed mortgage professionals who work for you, not the lender."* <br>**`More lenders, one application`** — *"We compare options from banks, credit unions and other lenders."* <br>**`Your information stays private`** — *"Detailed financial and identity information stays inside our secure application."* <br>Keeps the privacy signal, drops the housekeeping lecture. | [owner] |
| C-19 | 31–34 | Hero eyebrow "Mortgage guidance"; title "Start with your mortgage goal. Continue securely when you're ready." | Eyebrow: "Ontario mortgage brokerage". Title: *"Your mortgage, handled properly."* (or keep current title — it is not wrong, just neutral). | [owner] |
| C-20 | 34 | Description: "Explore common mortgage topics, ask a general question, or continue to the mortgage application when you are ready to provide detailed information." | *"Buying, renewing or refinancing? Compare options from multiple lenders, ask us anything, and apply online in a secure application."* | [owner] |
| C-21 | 40–45 | Buttons "Explore mortgage topics" / "Get started" | "See your options" / "Start your application" | [owner] |
| C-22 | 74–78 | "Where would you like to begin?" + "Choose the topic closest to your current goal. These pages provide general information and do not determine eligibility, rates or approval." | Keep heading. Body → *"Start with the topic that matches where you are today. It's general information — your rate and approval depend on your full picture."* (retains the required non-determination statement) | [safe] |
| C-23 | 96–99 | "How it works / A clear first step" + **four-sentence description that duplicates the numbered steps below it** | Eyebrow "How it works". Heading → *"Three steps, no runaround."* Body → *"Tell us what you need. Ask anything you like — you won't be asked for documents until you're ready. When you are, we move you into a secure application."* | [owner] |
| C-24 | 120–128 | **Eyebrow "Prefer to contact a specific agent?" and heading "Browse currently published profiles and choose an agent to contact." and an identical paragraph.** | Eyebrow "Work with one person". Heading *"Choose the agent you'd rather work with."* Body *"See who works in your area, then start with the person you pick."* — deletes the verbatim duplication and the word "published". | [owner] |
| C-25 | 133–145 | Aside: "Keep sensitive information out of general messages." + long list (SIN, banking, tax records, identity documents, passwords, mortgage documents) | Heading *"Never email us sensitive documents."* Body *"For your protection, we never ask for a SIN, banking details, tax records or ID by email or in a general form. Everything detailed happens inside the secure application."* | [safe] |
| C-26 | 174–181 | CTA band "Choose your next step / Ask a general question or continue to the mortgage application." | "Ready when you are / Ask a question, or start your application." | [safe] |

### 4.3 Find an Agent — `app/(public)/agents/page.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-27 | 26–28 | Hero description: "**Browse currently published profiles and select an agent to contact.**" | **Delete the description.** Make `description` optional in `PageHero` (`lib/public-components.tsx` L59) and omit it here — shortens the hero, as intended. If kept, use: *"Work with a licensed Keeper Financial mortgage agent."* | [owner] |
| C-28 | 31–34 | `<section aria-labelledby="agent-directory-heading">` + `<h2 id="agent-directory-heading">Agent directory</h2>` | **Delete the `h2` and the `aria-labelledby`** (or replace with `aria-label="Keeper Financial agents"` so the section keeps an accessible name). Frees vertical space so the agent grid sits higher. | [safe] |
| C-29 | 59 | `<p className="eyebrow">Published profile</p>` on every card | **Delete the line entirely.** | [safe] |
| C-30 | 62 | "Licence {number}" | Keep ("Licence {number}") — or "Licensed mortgage agent · {number}" if the agent licence type is confirmed. | [owner] |
| C-31 | 64 | "Serving {areas}" | "Serving {areas}" — keep. | [safe] |
| C-32 | 71 | "View profile" | "View profile" — keep, or "See full profile". | [safe] |
| C-33 | 36–38 | ErrorState: "Agent profiles are temporarily unavailable" / "Please try again later or contact Keeper Financial." | *"We can't show our agent list right now."* / *"Please try again shortly, or call or email us and we'll match you with an agent."* | [safe] |
| C-34 | 40–42 | EmptyState: "No agent profiles are available right now" / "Contact Keeper Financial for general assistance." | *"Our agent profiles are coming soon."* / *"In the meantime, call or email us and we'll connect you with the right agent."* | [owner] |
| C-35 | 9–13 | metadata description "Browse currently published Keeper Financial agent profiles." | "Meet the licensed mortgage agents at Keeper Financial and contact the one you'd like to work with." | [safe] |

> **Product note (owner decision):** because no agent profile is currently published, this page renders only the empty state today while "Find an Agent" sits in the main navigation. Consider hiding the nav item until at least one profile is live.

### 4.4 Agent profile — `app/(public)/agents/[slug]/page.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-36 | 70 | eyebrow "Keeper Financial agent" | "Licensed mortgage agent" | [owner] |
| C-37 | 108 | `<h2>Approved public contact</h2>` | `<h2>Contact</h2>` ("approved" is internal vocabulary) | [safe] |
| C-38 | 139 | eyebrow "Brokerage identity" | "Brokerage information" (matches `/about`) | [safe] |
| C-39 | 148–151 | fine print: "Agent-specific application attribution is managed through Keeper Financial's application configuration." | **Delete.** Pure implementation detail published to the public. | [safe] |
| C-40 | 29–31 | noindex fallback description "No approved Keeper Financial agent profile is published at this address." | "This agent profile isn't available." (title: "Agent profile not available") | [safe] |
| C-41 | 91–105 | "Services and languages" with `Languages / Service areas / Specialties` | Keep — accurate and useful. Consider "Languages, areas and specialties". | [safe] |

### 4.5 How it works — `app/(public)/how-it-works/page.tsx` + `lib/public-content.ts`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-42 | page 21 | "Begin with general information and basic contact details. Move to the mortgage application only when you are ready to provide detailed information." | *"Ask us anything general first. When you're ready to apply, we'll take you into a secure application — no documents needed until then."* | [safe] |
| C-43 | content 374–377 (`processSteps[1]`) | "Share your name, contact details, general mortgage goal and non-sensitive context." | *"Share your name, contact details and a short note about what you need."* | [safe] |
| C-44 | content 379–382 (`processSteps[2]`) | "Use the configured mortgage application service for detailed financial, credit, identity and document information." | *"Continue in our secure application, where your financial, credit and identity details belong."* | [safe] |
| C-45 | page 51 | bullet "A brief, non-sensitive message" | "A short message" | [safe] |
| C-46 | page 56–61 | "What belongs in the application" / "Provide detailed income, assets, liabilities, credit consent, identity information and mortgage documents only through an authorized secure process." | Heading *"What stays in the secure application"*. Body *"Income, assets, debts, credit consent, ID and documents — never by email and never in a general form."* | [safe] |
| C-47 | page 67–70 | "Keep expectations clear" / "Public information cannot determine your outcome." | Eyebrow *"What to expect"*. Heading *"Real answers for your situation."* Body → *"What's on this website is general information. Once we understand your goals and your details, we can tell you what's realistic — and what isn't."* (keeps the honest non-determination message) | [owner] |
| C-48 | page 86–92 | CTA "Start in the way that suits you / Ask a general question or move directly to the mortgage application." | "Start in the way that suits you / Ask a question, or go straight to the application." | [safe] |

### 4.6 Mortgages hub — `app/(public)/mortgages/page.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-49 | 22 | Title "Information for the mortgage decision in front of you." | *"Mortgage help, wherever you are right now."* | [owner] |
| C-50 | 23 | "Review common mortgage topics in plain language. When you are ready, you can ask a general question or continue to the mortgage application." | *"Buying your first home, renewing, refinancing or investing — start with plain-language answers, then talk to a licensed professional."* | [owner] |
| C-51 | 36–39 | "Choose a topic" + "This information is general. It does not advertise a rate, determine eligibility, or replace a review of your complete circumstances." | Keep both (this is the required disclosure) — tighten second sentence to *"It's general information: it doesn't quote a rate, decide eligibility, or replace a review of your situation."* | [legal] [safe] |
| C-52 | 55–58 | eyebrow "A useful boundary" — heading "General information here. Detailed information in the application." (repeated on mortgage detail pages) | eyebrow *"Where to start"*. Heading *"General questions here. Detailed information in your secure application."* | [safe] |
| C-53 | 61–69 | "Use this website for general information and basic contact details. Provide income, assets… only through an authorized secure process." / "the Get Started page links through a validated route to the configured mortgage application service." | *"Ask us anything general, or give us your contact details. Income, assets, debts, credit consent, ID and documents go in the secure application — never by email."* / *"When you're ready, Get started takes you straight to the secure mortgage application."* | [safe] |
| C-54 | 76–82 | CTA "Not sure where to begin? / Start with a general question and keep sensitive information out of your message." | "Not sure where to begin? / Ask us a question — you don't need to share anything detailed yet." | [safe] |

### 4.7 Mortgage detail — `app/(public)/mortgages/[slug]/page.tsx` + `lib/public-content.ts`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-55 | page 99 | `<h2>Consider:</h2>` | `<h2>Worth thinking about</h2>` (colon reads like an editor's note) | [safe] |
| C-56 | page 106–117 | The **aside repeats verbatim** what the section at 121–138 says — the boundary is stated three times on one screen (aside, section, and again in the CTA area of `/mortgages`). | **Delete the aside on detail pages**; keep the single "Protect sensitive information / Use the right channel for each step" section. | [safe] |
| C-57 | content 160 / 202 / 245 / 284 / 328 (`lead`, = metadata description) | "Understand the mortgage steps that may form part of a planned home purchase and prepare questions before beginning a complete application." *(and the equivalent leads for refinance/renewal/FTHB/investment)* | Rewrite each lead as a benefit/plain-language promise, e.g. <br>Purchase: *"What usually happens between 'we're thinking about buying' and getting the keys."* <br>Refinance: *"Change your amount, term or structure — and know the costs before you commit."* <br>Renewal: *"Your lender's renewal letter isn't your only option. Here's what's worth comparing."* <br>First-time buyers: *"A step-by-step look at your first purchase, from budget to keys."* <br>Investment: *"Investment mortgages work differently — here's what matters before you commit."* | [owner] |
| C-58 | content 164–168 etc. (`considerations`) | "when detailed financial information and documents may be required through the mortgage application" | *"when we'll need your financial details and documents (always inside the secure application)"* | [safe] |
| C-59 | content 165–195 (`sections[].points`) | Lowercase fragments: "how a purchase amount is assessed", "term and rate-structure options in plain language", "costs that sit outside the mortgage itself" | Sentence case and consistent phrasing across all five products: *"How a purchase amount is assessed"*, *"Term and rate options, in plain language"*, *"Costs outside the mortgage itself"*. | [safe] |
| C-60 | content 24–31 (`brokerSummary`) | eyebrow "Why work with a broker" / "Mortgage guidance built around your options" | Keep (approved copy) — but it duplicates the `/broker` H1/eyebrow block. Consider eyebrow *"Why a broker"*. | [legal] |

### 4.8 Get started — `app/(public)/apply/apply-paths.tsx`, `apply/apply-form.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-61 | paths 21–24 | H1 "Choose how you'd like to begin" / "Ask a general question using basic contact details, or continue to the mortgage application when you are ready to provide detailed information." | H1 keep. Body → *"Ask us a question with just your contact details, or start your private application when you're ready to share more."* | [safe] |
| C-62 | paths 25–29 | notice: "Do not submit financial, identity, health, credential, or underwriting information in the contact form. Use the secure full-application path for detailed mortgage information." | *"Please don't send financial, identity or health details in the contact form — the secure application is the place for those."* (drops "credential"/"underwriting" jargon) | [legal] [safe] |
| C-63 | paths 40–42 | "Share your name, contact details, general mortgage objective and optional non-sensitive context." | *"Share your name, contact details and a short note about what you need."* | [safe] |
| C-64 | paths 62–67 | eyebrow "Option two" / H2 "Continue to the mortgage application" / "Start a private, same-browser Keeper application for detailed financial, identity, property and mortgage information." | Keep H2 (it is also a tested link name). Body → *"Start your private application for the financial, identity and property details we'll need. It saves as you go in this browser only."* | [safe] |
| C-65 | paths 74–81 | fine print (see C-09) plus "Do not use a shared device." | *"Saved as you go. Your draft resumes only in this browser, so please don't use a shared or public device."* | [safe] |
| C-66 | form 247–251 | "Brief message (optional)" hint: "Do not include a SIN, banking information, tax records, credit information, passwords, identity documents or mortgage documents." | Shorten to *"Please don't include your SIN or banking details here."* — the full list already appears in the page notice and the aside. | [legal] [safe] |
| C-67 | form 164–168 | success notice: "Your contact request has been received. Keep sensitive information out of follow-up email. Use an authorized secure process if documents are requested." | *"Thanks — your request has been received. For your protection, please don't send documents by email; we'll point you to the secure application if we need them."* | [safe] |
| C-68 | form 258–259 | "I agree that Keeper Financial may contact me about this service inquiry. **Required.**" | Keep the consent (do not reword a consent statement casually). Optional style fix: *"I agree that Keeper Financial may contact me about this enquiry."* | [legal] |
| C-69 | form 262–263 | "I would also like optional marketing communications. This is separate and not required for service." | Keep (CASL-relevant) — clear and accurate. | [legal] |

### 4.9 Contact — `app/(public)/contact/page.tsx`

The same "don't send documents" warning currently appears three times on this page (hero description, email card, aside) and again on `/apply`.

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-70 | 20–21 | "Start with a general question." / "Call, email or send a basic contact request. Keep financial, identity and mortgage documents out of general messages." | Title keep. Body → *"Call, email or send us a message — we'll get back to you. (Anything detailed belongs in the secure application.)"* | [safe] |
| C-71 | 29–31 | Call card: "Speak with Keeper Financial about a general mortgage question or mortgage review." | *"Talk to a licensed mortgage professional about what you're trying to do."* | [safe] |
| C-72 | 40–42 | Email card: "Use email for general questions only. Do not attach mortgage, financial, tax, or identity documents." | *"Email us for anything general. Please don't attach documents — we'll ask through the secure application."* | [safe] |
| C-73 | 57–61 | eyebrow "Send a contact request" / "Share only what the team needs to respond." / "The Get Started form collects basic contact details, a general mortgage objective, and optional non-sensitive context." | eyebrow *"Send us a message"*. Heading *"Tell us what you need."* — **delete the third sentence** (describing your own form to the visitor is internal thinking). | [safe] |
| C-74 | 62–64 | Button "Go to Get Started" | "Send a message" | [safe] |
| C-75 | 66–73 | aside "Do not send sensitive information" + long list | Keep as the **single** sensitive-information panel on the page (then trim the hero/email duplicates per C-70/C-72). | [safe] |

### 4.10 About — `app/(public)/about/page.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-76 | 20–21 | "Mortgage information and a clear way to take the next step." / "Keeper Financial helps people understand common mortgage processes, ask general questions and continue to a complete application through an authorized secure process." | *"A mortgage brokerage built around clear advice."* / *"We're a licensed Ontario brokerage. We'll help you understand your options, answer the questions that matter, and guide you through the application — start to finish."* | [owner] |
| C-77 | 31–33 | "Our approach" / "Start with understanding. Continue with purpose." | Keep eyebrow. Heading → *"Advice first. Paperwork later."* | [owner] |
| C-78 | 36–45 | Two paragraphs about the public site's separation of channels ("The public website is designed to help people understand common mortgage paths before they are asked for detailed information… This separation supports a simpler experience…") | Replace with a **customer-facing** statement: *"We start with a conversation. Ask us anything — no documents, no pressure. When you're ready to apply, we move you into our secure application and keep your details protected end to end."* (The current text describes site architecture, not the brokerage.) | [owner] |
| C-79 | 53–54 | "Plain language" / "We explain the next step without unnecessary jargon." | Keep. | [safe] |
| C-80 | 58–62 | **"Information minimization"** / "Public contact routes request only basic information needed to respond." | *"Your privacy"* / *"We ask for only what we need, when we need it."* | [safe] |
| C-81 | 66–70 | "Secure handoff" / "Detailed mortgage information and documents belong in the mortgage application or another authorized secure channel." | *"Security by design"* / *"Detailed financial and identity information stays inside your private application."* (If the word "encrypted" is used, it needs the claim review below.) | [legal] [owner] |
| C-82 | 78–79 | eyebrow "Published identity" | *"Who we are"* | [safe] |
| C-83 | 94–95 | "These are the current published public contacts. Do not email sensitive mortgage or identity documents." | *"Please don't email sensitive mortgage or identity documents."* | [safe] |
| C-84 | 103–104 | CTA "Let's start with your general goal" / "Use a real contact route or compare both paths on Get Started." | *"Let's start with your goal"* / *"Call, email, or see both ways to begin."* ("a real contact route" is internal language and meaningless to a visitor.) | [safe] |

### 4.11 Careers — `careers/page.tsx`, `careers/[slug]/page.tsx`, `lib/public-content.ts`

The recruitment copy was owner-approved 2026-07-29 and is the strongest public copy on the site. Only the "published"/"opportunity" vocabulary and empty-state wording need work.

| # | File · line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-85 | content 92 | eyebrow **"Published roles"** | "Open roles" | [owner] |
| C-86 | content 94 | "Review each published opportunity before choosing the role you want to apply for." | "See what's open, then apply for the role that fits you." | [owner] |
| C-87 | page 56–58 | "No opportunities are currently published" / "Check this page again later for future opportunities." | *"No open roles right now."* / *"New mortgage agent opportunities are posted here as they open — check back soon."* (must not invite résumés: `docs/06` L112 forbids a résumé inbox / new candidate-data path) | [owner] |
| C-88 | page 41–42 | Error: "Opportunities are temporarily unavailable" / "Please try again later." | *"We can't load our current openings right now."* / *"Please refresh or try again shortly."* | [safe] |
| C-89 | page 73 | eyebrow "Featured opportunity" | "Now hiring" | [owner] |
| C-90 | page 106 | "View opportunity" | "View role" | [safe] |
| C-91 | slug 54 | eyebrow "Current opportunity" | "Current role" | [safe] |
| C-92 | slug 65–66 | eyebrow "Role overview" + H2 "Opportunity details" | Collapse to a single heading: *"About the role"* | [safe] |
| C-93 | content 459–461 | application lead: "Choose the entry path that fits you. Both options keep your application tied to this exact opportunity." | "Choose the path that fits you. Both keep your application tied to this role." | [safe] |
| C-94 | content 433–435 | journey step 1: "Review the published opportunity" / "Read the role details without creating an account." | "Review the role" / "Read the details — no account needed." | [safe] |
| C-95 | content 437–439 | step 2: "Create an account and save a draft" / "Begin a posting-specific application and return to your saved draft in the candidate portal." | "Create an account and start" / "Start your application and pick it up any time from the candidate portal." | [safe] |
| C-96 | content 441–443 | step 3: "Follow your application" / "View candidate-visible status updates and messages through the portal." | "Track your progress" / "See your status and messages in the portal." | [safe] |
| C-97 | content 474–476 | step 4: "Onboard if selected" / "Selection may lead to Keeper's controlled onboarding process." | "Onboard if you're selected" / "Selected candidates move into our onboarding process." | [safe] |
| C-98 | content 462–472 | application steps "Choose your account path" / "Prepare your application" / "Follow status and messages" / "Onboard if selected" | "Create your account" / "Complete your application" / "Track status and messages" / "Onboard if selected" | [safe] |

**Careers must not gain:** awards, rankings, "best"/"leading" comparisons, testimonials, earnings or growth statistics, invented lead volumes, lender counts, or timelines (`docs/06` L109; enforced by `tests/public-source-safety.test.ts`).

### 4.12 Complaints — `complaints/page.tsx`

Regulatory content — polish only, and any change needs sign-off (approved 2026-07-23, `docs/09` L114).

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-99 | 18 | Hero description duplicates the first section's first sentence **verbatim** ("Keeper Financial takes client concerns seriously. If you have a complaint about the mortgage services you received, please contact us so we can review the matter.") | Hero: *"If something went wrong, we want to hear about it and make it right."* (the detailed sentence stays in the section below) | [legal] |
| C-100 | 22–28, 121–133 | FSRA escalation, "does not guarantee a specific outcome", rights-preservation note | **Keep verbatim.** | [legal] |

### 4.13 Accessibility — `accessibility/page.tsx`

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-101 | 22–51 | Bullet list in engineering terms ("Keyboard-operable navigation and interactive elements", "Error and status messages that do not rely on colour alone", "Content that reflows on smaller screens without page-level horizontal scrolling") | Keep the substance, plain-language it: *"Clear page structure and headings"*, *"Works with a keyboard"*, *"Visible focus indicators"*, *"Every form field is labelled"*, *"Reflows on small screens without side-scrolling"*, *"Status messages that don't rely on colour"*, *"Readable contrast"*, *"Respects reduced-motion settings"*, *"Descriptive link text"*, *"Alternative text for meaningful images"*. | [legal] |
| C-102 | 98–113 | WCAG 2.1 AA commitment + commitment paragraph | **Keep.** | [legal] |
| C-103 | 122–127 | (see C-07) internal release-planning paragraph | **Delete.** | [legal] |

### 4.14 Privacy Notice — `privacy-policy/page.tsx`

See P0-1 … P0-3. Additionally:

| # | Line | Current | Proposed | Sign-off |
|---|---|---|---|---|
| C-104 | 87–95 | Two consecutive `<h1>`-style appearances: page header "Privacy Notice" plus the article's retained "Privacy Notice" body text | The `APPROVED_CONTENT.slice(3)` manipulation removes the first three lines but the notice still opens with "This notice describes how Keeper Financial Inc.…". Consider titling the article "What this notice covers". | [legal] |
| C-105 | 5–58 | The whole notice is a single template literal with a fragile `slice(3)` + blank-line splitter | Recommend structuring the notice as typed data (heading/paragraph arrays) like the rest of `public-content.ts` — a content-safety change, not decoration. | [safe] |

---

## 5. Structural changes to reduce frame height and repetition

These are the layout-affecting items the owner asked for. They are cheap but touch CSS/aria, so list them separately for the dev agent.

| # | Change | Files | Notes |
|---|---|---|---|
| S-1 | Delete the `Agent directory` `h2`; keep the grid | `app/(public)/agents/page.tsx` L31–34 | Update/remove `aria-labelledby`. `.grid-2.agent-directory-grid` already sets `min-width:0` + `overflow-wrap:anywhere` (globals.css L807) — no CSS change needed for 2-up cards. |
| S-2 | Remove the agents hero description | `agents/page.tsx` L27 + `lib/public-components.tsx` L59 (`description?: string`) | Shortens the hero band; `.page-hero-copy` padding is `clamp(4rem,8vw,7.5rem)` (globals.css L975). |
| S-3 | Delete the duplicated home "contact an agent" paragraph | `app/(public)/page.tsx` L126–128 | Heading and paragraph are currently identical strings. |
| S-4 | Replace the home trust-strip chain (C-18) | `app/(public)/page.tsx` L49–70 | `.trust-strip` is a 3-column grid; keep exactly three `<div>`s or the `> div + div` divider rule (globals.css L1051) misbehaves. |
| S-5 | Collapse the home "How it works" description (C-23) | `app/(public)/page.tsx` L96–99 | The description currently restates all four `processSteps` beneath it. |
| S-6 | Delete the mortgage-detail boundary aside (C-56) | `mortgages/[slug]/page.tsx` L106–117 | Removes a third statement of the same boundary on one screen; `.reading-grid.detail-consider` then holds one card. |
| S-7 | Trim the "do not send documents" message from 6 surfaces to 3 | home aside, `/apply` notice, `/contact` aside, `/how-it-works` aside, `/mortgages` section, `/broker` section, mortgage-detail section | Keep one statement per page maximum. |
| S-8 | Remove "Published profile" from cards and all "published*" strings site-wide | `agents/page.tsx` L59; `about` L78/L94; `careers` content L92/L433; home L122/L127; `agents` metadata L11 | Grep `published` across `app/(public)` and `lib/public-content.ts` after the change — the term must not appear in public copy except in the Privacy Notice's legal retention language. |

---

## 6. Proposed home-page messaging (owner decision)

The home page currently spends its first scroll on boundary housekeeping. For an Ontario brokerage landing page, the recommended order is:

1. **Hero** — who we are + what the visitor gets (C-19/C-20). Keep the image and the two buttons.
2. **Trust strip** — three value statements: licensed professionals · multiple lenders · private and secure (C-18).
3. **"Where would you like to begin?"** — unchanged topic cards (they are good and already approved).
4. **How it works** — three steps, no repetition (C-23).
5. **Broker credibility band** — *new, optional*: lift two or three approved `/broker` statements ("A broker helps you compare options from multiple lenders…", "No broker can guarantee approval — and that's a good thing for you to know") onto the home page with a link to `/broker`. This is the single highest-value addition the review recommends, and it needs the claims review below.
6. **Agent band** — "Choose the agent you'd rather work with" (C-24).
7. **Careers band** — unchanged (approved).
8. **CTA** — unchanged.

**Any new public claim must pass `docs/04` L232 ("Public claims, titles, testimonials, and marketing content require controlled review") and `docs/06` L109.** No rates, no "5-star rated", no "60+ lenders", no approvals, no invented timelines — `tests/public-source-safety.test.ts` fails the build on several of those strings.

---

## 7. Do not touch (regulated, approved, or legally load-bearing)

Keep verbatim unless legal/owner approves a replacement:

1. `FSCO # 13696` regulatory line — recorded as owner-supplied and **still pending legal/regulatory approval of the presentation** (`docs/09` L57, L114; `docs/17` L124). *(Separately: FSCO was superseded by FSRA as the regulator; the displayed registration text should be verified with the owner/legal. Do not self-correct this.)*
2. Footer: "Mortgage options are subject to borrower qualification and lender approval."
3. `brokerInfoSections` no-guarantee section, "General information only" disclosure, and the FTHB GST/HST rebate CRA link.
4. `/complaints` FSRA escalation, complaint procedure, and rights-preservation note.
5. `/accessibility` WCAG 2.1 AA commitment and alternative-format commitment.
6. Privacy Notice structure, purposes, disclosure, and rights language (fix only the defects in P0-1/2/3 with legal sign-off).
7. The borrower application's **versioned privacy/credit-use consent wording text** (server-supplied; approved 2026-07-27, `borrower-privacy-credit-disclosure-2026-07-27-v1`).
8. The service/marketing consent separation in the contact form.
9. Contact details, address, phone, email, `siteConfig` values.

---

## 8. Test and documentation impact (the dev agent will break these)

**Tests that assert copy and must be updated in the same commit:**

| Test | Assertion coupled to copy |
|---|---|
| `apps/web/tests/public-pages.test.tsx` | Home recruitment teaser `h2` "Build your mortgage business. Keep more control." + link "Explore careers at Keeper" (L36–43); careers `h1` (L60–63); agents `h1` "Find a Keeper Financial agent" (L78–83) — **C-27/C-28 affect this** |
| `apps/web/tests/apply-page.test.tsx` | `h1` "Choose how you'd like to begin" (L18–20); "Continue to the mortgage application" heading + link (L24, L46–54) — **C-61/C-64 affect these** |
| `apps/web/tests/apply-form.test.tsx` | validation strings (L46–56), `/Do not include a SIN/i` (L67) — **C-66 affects this**; response messages (L154), unavailable-contact string (L170) — **C-11 affects this** |
| `apps/web/tests/seo.test.ts` | **titles and descriptions must stay unique across all 11 static pages + 5 mortgage pages** — any V2 rewrite of `mortgageServices[].title/lead` or page metadata must preserve uniqueness |
| `apps/web/tests/public-shell.test.tsx` | nav "Get started", `regulatoryText`, address (L14–38) |
| `apps/web/tests/public-source-safety.test.ts` | forbidden invented facts (`$1.48M`, `4.49%`, `60+ lenders`, `5-star rated`, `NMLS`, mock names) — **hard guardrail for any new marketing copy** |
| `apps/web/tests/accessibility-regressions.test.tsx` | exactly one `main` landmark with `id="main-content"` on public routes — do not restructure the agents section into an extra wrapper that breaks this |

**Documents to update in the same branch (living docs only):**

- `docs/06_UX_UI_IMPLEMENTATION_GUIDE.md` — product-experience principles still say "Plain language … Avoid unnecessary financial jargon" (L31–42): add the concrete vocabulary rule (no "published", "configured", "validated route", "authorized secure process" in public copy), and update the `/apply` page requirements (L56–76) to match C-09/C-65.
- `docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md` — new dated entry recording the public-copy review, the vocabulary standard, and each approved before/after decision; annotate the 2026-07-23 complaints/accessibility/broker approvals if those pages change.
- `docs/00_PROJECT_SOURCE_OF_TRUTH.md` → checkpoint note.
- `docs/15_KNOWN_LIMITATIONS.md` — if C-09 removes the "final submission not available" disclosure, the limitation inventory must record the actual production gate (real-data submission fail-closed).
- `docs/26_PHASE_1F_..._READINESS_PLAN.md` — the privacy/claims/advertising review rows: point them at the corrected Privacy Notice (P0-2/P0-3 change the scope of that review).
- `docs/04_SECURITY_PRIVACY_COMPLIANCE_BASELINE.md` L232 — remains the gate for any new public claim.

Do **not** edit `docs/17`, `docs/25`, `docs/27`, `docs/28`, `docs/34`, `docs/35` (historical reports) — they are evidence of their original review moments.

---

## 9. Delivery plan (executed)

One unit of work, one branch, one writer (per `AGENTS.md`). **Executed on
`content/public-copy-review` as three commits** — see §0 for the actual commit split; the
four proposed units were consolidated into one copy commit (with its test updates, so no
commit lands with red tests), one docs commit, and a follow-up heading-order fix.

```
git fetch origin --prune
git checkout main && git merge --ff-only origin/main
git checkout -b content/public-copy-review
```

Commit in four logical units, in this order:

1. `fix(web): correct privacy notice, accessibility and apply-page copy defects` — P0 only (C-01…C-13).
2. `refactor(web): remove internal vocabulary from public copy` — the §3 vocabulary pass + S-8, no structural change.
3. `feat(web): tighten public page framing and remove duplicate copy` — §4 page rewrites + §5 structural changes.
4. `test(web): update public copy assertions and content safety guards` — §8 test updates (must accompany 2 and 3 in the same PR; do not land copy alone with red tests).

Docs commits go with the corresponding code commit.

**Validation (must be green before PR):**

```
cd apps/web && npx prettier --check app lib tests *.ts *.mjs   # CI runs this
npm run lint --workspace @keeper/web
npm run typecheck --workspace @keeper/web
npm test --workspace @keeper/web
cd ../.. && make test
```

`tsc --noEmit` may need `rm -rf apps/web/.next` first if routes were renamed (not expected here). `make migrate-check` is not affected — this change touches no model or schema metadata.

Then confirm the copy changes on the rendered pages (the repository copy files are the same ones that render live, so a local `npm run dev` or the staged preview is sufficient evidence), and ask the owner before push/PR/merge.

---

## 10. Owner decisions (all approved 2026-10-16)

All eight questions below were answered by the owner with legal sign-off on 2026-10-16
(decision 50): item 1 was answered **(a) remove the stale statement**; items 2–7 were
approved as proposed; item 8 confirmed that every `[owner]`/`[legal]` row is explicitly
approved. The navigation question was answered as **keep "Find an Agent"**, so C-16 was not
applied.


1. **P0-5** — publish option (a) remove, or (b) soften the "final submission not available" statement while the real-data gate is on.
2. **P0-2/P0-3** — approve corrected Privacy Notice wording (Filogix removal + a borrower-application section); this is a legal/privacy deliverable.
3. **P0-1** — approve the retention sentence, or authorise deleting the placeholder block.
4. **§6** — approve promoting approved `/broker` credibility copy onto the home page (claims review required).
5. **C-18/C-19/C-20** — approve the new home hero and trust-strip messaging and the claim wording ("licensed professionals", "multiple lenders", "private and secure").
6. **C-14/C-17** — approve the footer/root tagline rewrite.
7. **C-34 + nav** — decide whether "Find an Agent" stays in the public nav while no agent profile is published.
8. **C-01…C-105 sign-off split** — confirm the dev agent may apply all `[safe]` rows mechanically, and that `[owner]`/`[legal]` rows wait for explicit approval.
