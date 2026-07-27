# Phase 1A Public Website Implementation Report

Date: 2026-07-14

Branch: `feature/phase-1a-public-site`

## Outcome

Phase 1A is engineering-complete as a public Next.js website implementation while the Phase 0 FastAPI modular monolith, PostgreSQL authority, Supabase identity/application authorization split, lead minimization/consent/abuse controls, private storage boundary, lifecycle services, audit behavior, and fail-closed environment rules remain intact.

This is not owner/legal/production approval. Final legal and regulatory wording, formal privacy/complaints/accessibility contacts and processes, image/font/logo licensing, manual accessibility review, production hosting, and production operations remain required. No mortgage origination, borrower financial-data store, candidate workflow, onboarding, agent-publication workflow, CRM, commission, payroll, custom e-signature, or fabricated vendor behavior was added.

## Delivered public routes

| Route                               | Delivered behavior                                                                                         |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `/`                                 | Responsive split-image home, service entry points, process, privacy boundary, recruitment entry, and CTAs. |
| `/mortgages`                        | Educational mortgage-services landing.                                                                     |
| `/mortgages/purchase`               | Purchase-mortgage education.                                                                               |
| `/mortgages/refinancing`            | Refinancing education.                                                                                     |
| `/mortgages/renewals`               | Renewal education.                                                                                         |
| `/mortgages/first-time-buyers`      | First-time-buyer education.                                                                                |
| `/mortgages/investment-properties`  | Investment-property mortgage education.                                                                    |
| `/how-it-works`                     | Plain-language contact-to-secure-application process and data boundary.                                    |
| `/about`                            | Brokerage approach plus controlled public identity/contact facts.                                          |
| `/contact`                          | Real `tel:`, `mailto:`, office address, and minimal-contact route.                                         |
| `/apply`                            | Existing minimal lead form and validated external application path inside the approved visual shell.       |
| `/careers`                          | Polished public recruitment presentation and honest no-approved-postings state; no candidate workflow.     |
| `/agents`                           | Honest no-approved-public-profiles state; no database record exposure.                                     |
| `/privacy`                          | Current engineering privacy/data-boundary notice with explicit legal-review limitation.                    |
| `/complaints`                       | Real complaint contact routes with explicit missing escalation/timeline limitation.                        |
| `/accessibility`                    | Implemented accessibility approach and real feedback contacts with audit limitation.                       |
| `/agents/[slug]`, `/careers/[slug]` | Non-public behavior until approved Phase 1E/1C publication queries exist.                                  |
| `/robots.txt`, `/sitemap.xml`       | Generated crawler controls and public-only discovery inventory.                                            |

Protected `/candidate/**` and `/admin/**` routes retain their server-side portal authorization checks. `/auth/sign-in`, candidate, and admin metadata/robots controls prevent indexing.

## Shared visual system and components

- `packages/ui/src/tokens.css`: paper/ink/surface/gold/charcoal palette, spacing, radii, shadows, content widths, and semantic state colors.
- `packages/ui/src/components.tsx`: existing accessible form/state/table/timeline/dialog primitives plus reusable `SectionHeading` and keyboard-native `Disclosure`.
- `apps/web/lib/public-components.tsx`: line icons, responsive `PageHero`, `ServiceCard`, `CtaBand`, and `InteriorPageHeader`.
- `apps/web/lib/shells.tsx`: semantic text/CSS Keeper lockup, desktop navigation, keyboard-native mobile navigation, structured organization facts, public footer, real contact actions, and preserved portal shell.
- `apps/web/app/globals.css`: split heroes, trust bands, cards, process/list layouts, policy/apply states, recruitment treatment, focus, reduced-motion, and 320px-oriented reflow rules.

The agent-profile mockup informed only the shared visual language. No dashboard, leads, clients, applications, documents, rates, production, pipeline, appointment, activity, testimonial, resource, or CRM functionality was copied.

## Controlled content and public facts

- `apps/web/lib/public-content.ts` is the typed repository-controlled Phase 1A content mechanism. No CMS, page builder, database-backed public copy, or vendor integration was introduced.
- `apps/web/lib/site-config.ts` validates browser-visible owner-controlled values and safely falls back only to the owner-supplied public facts.
- `.env.example` configures `Keeper Financial`, `Keeper Financial Inc.`, exact regulatory text `FSCO # 13696`, `380 Wellington Street, Tower B, 6th Floor, London ON, N6A 5B5`, `support@keeperfinancial.ca`, `+1 (709) 700-7339`, and `https://apply.keeperfinancial.ca/`.
- The FastAPI application redirect continues to require HTTPS, exact allowed host `apply.keeperfinancial.ca`, no credentials/query/fragment, and configuration-only destinations.
- `NEXT_PUBLIC_BOOKING_URL` and `NEXT_PUBLIC_PRINCIPAL_BROKER` are empty. Unsafe/missing booking URLs fail closed; no principal broker is inferred or displayed.

## Mockup translation and raster assets

The approved references share an ivory paper ground, editorial serif display type, compact sans body type, warm restrained gold, charcoal trust/CTA bands, thin borders, low shadows, split photography, compact service cards, and generous vertical rhythm. Phase 1A maps those characteristics into shared tokens and reusable compositions rather than screenshot backgrounds or page-specific copies.

Two 1536 × 1024 photography-only PNG assets were created with the built-in `imagegen` workflow and stored under `apps/web/public/images`. The home mockup was the style/composition reference for `home-conversation.png`; the recruitment mockup was the reference for `recruitment-team.png`. Prompts required photorealistic-natural editorial scenes, right-weighted crop-safe subjects, warm neutral palettes, and no text, logo, UI, readable documents, claims, badges, figures, watermarks, or identifiable reference people. Exact hashes and source mapping are in `docs/ui/README.md`.

No standalone mockup crop, mockup UI text, example data, or full screenshot is used in production. The CSS/text lockup is intentional because no approved standalone vector logo was supplied.

## Accessibility controls

- Skip navigation and semantic header/nav/main/footer landmarks.
- Native links, buttons, form controls, `details`/`summary` mobile navigation, and disclosures.
- Visible high-contrast focus outline; no hover-only navigation.
- Labelled form fields, hints, separate consent controls, error summary, live success status, loading/error/empty/not-found states, and non-colour status language.
- Explicit `min-width: 0`, page overflow protection, single-column narrow layouts, crop-safe images, practical target sizes, and smallest-breakpoint full-width actions.
- Reduced-motion handling and no motion-dependent content.
- Meaningful image alt text, explicit aspect-ratio source dimensions, responsive `sizes`, and Next.js image optimization.
- Independent Codex review identified two P2 accessibility issues. Remediation changed accent-on-white text contrast to at least 4.5:1 through `#a36914` and restored `main#main-content` on the global 404 page.
- Regression tests cover both the accent/white contrast threshold and the global 404 main-content landmark.

Manual WCAG 2.1 AA, screen-reader, contrast, zoom, keyboard, cross-browser, and owner mobile review remain Phase 1F approval work.

## SEO and discovery controls

- Unique title/description metadata for every finished static public page and each mortgage-service route.
- Validated `metadataBase`, canonical URLs, Open Graph, Twitter summary metadata, and `en-CA` locale.
- Organization JSON-LD contains only approved public name, legal name, URL, email, phone, and address facts.
- Sitemap contains only finished static public routes; it excludes dynamic profile/posting slugs, auth, candidate, and admin routes.
- Robots disallows `/auth/`, `/candidate/`, and `/admin/`; private layouts are explicitly `noindex`, `nofollow`, `noarchive`.
- Dynamic agent and posting foundations are no-index and return not-found behavior.

## Test evidence

- Frontend: 10 Vitest files / 30 tests pass after the accessibility-review regressions were added. Coverage includes anonymous public rendering, unique metadata, sitemap/robots, public navigation/footer/contact facts, configuration fail-closed behavior, dynamic publication boundaries, mockup-claim leakage, narrow-screen CSS guardrails, apply minimization/consent, portal API authorization behavior, accent/white contrast, and the global 404 main-content landmark.
- Next.js production build passes and generates 30 static/SSG/dynamic routes without metadata, type, routing, hydration, or build errors.
- Existing backend tests continue to cover anonymous/identity-only/wrong-role/lifecycle access, minimal leads, separate consent evidence, sensitive/extra-field rejection, bot trap/rate limiting, lifecycle rules, private document isolation, health checks, redirect validation, and unsafe environment rejection.

The final full validation command-by-command results are recorded below after the requested clean rerun.

## Full validation results

The complete requested sequence passed in an external socket-enabled rerun on 2026-07-14.

| Command/check                                          | Result                                                                                                                                                                                                                                                        |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `docker compose config`                                | Pass.                                                                                                                                                                                                                                                         |
| `docker compose build`                                 | Pass for the API and web images.                                                                                                                                                                                                                              |
| `docker compose up -d`                                 | Pass.                                                                                                                                                                                                                                                         |
| `docker compose ps`                                    | Pass: PostgreSQL and API were healthy, and web was running.                                                                                                                                                                                                   |
| Recent service logs                                    | Pass: logs showed normal Next.js, Uvicorn, and PostgreSQL startup.                                                                                                                                                                                            |
| Public web route checks                                | Pass: `/`, `/mortgages`, `/mortgages/purchase`, `/how-it-works`, `/about`, `/contact`, `/apply`, `/careers`, `/agents`, `/privacy`, `/complaints`, `/accessibility`, `/robots.txt`, and `/sitemap.xml` returned HTTP 200; an unknown route returned HTTP 404. |
| API `/health` and `/health/db`                         | Pass: `/health` returned status `ok`, and `/health/db` reported the database reachable.                                                                                                                                                                       |
| `npm run format:check`                                 | Pass for web, contracts, and UI.                                                                                                                                                                                                                              |
| `npm run lint`                                         | Pass for web and UI with zero warnings.                                                                                                                                                                                                                       |
| `npm run typecheck`                                    | Pass for web, contracts, and UI.                                                                                                                                                                                                                              |
| `npm run test`                                         | Pass: 10 files, 30 tests.                                                                                                                                                                                                                                     |
| `npm run build`                                        | Pass: Next.js 16.2.10 compiled/typechecked and generated 30 routes/pages.                                                                                                                                                                                     |
| `.venv/bin/ruff check apps/api`                        | Pass.                                                                                                                                                                                                                                                         |
| `.venv/bin/ruff format --check apps/api`               | Pass: 41 files already formatted.                                                                                                                                                                                                                             |
| `.venv/bin/mypy apps/api/src`                          | Pass: 31 source files.                                                                                                                                                                                                                                        |
| `.venv/bin/pytest apps/api/tests`                      | Pass: 29 tests, 1 warning.                                                                                                                                                                                                                                    |
| `../../.venv/bin/alembic upgrade head` from `apps/api` | Pass.                                                                                                                                                                                                                                                         |
| `../../.venv/bin/alembic current` from `apps/api`      | Pass: `20260714_0001 (head)`.                                                                                                                                                                                                                                 |
| `git diff --check`                                     | Pass after final documentation update.                                                                                                                                                                                                                        |
| `git status --short --branch`                          | Clean branch identity with expected uncommitted Phase 1A modifications/untracked additions; exact status is included in the completion handoff.                                                                                                               |

## Owner decisions and assets still required

- Owner/legal approval of final `FSCO # 13696` presentation and all public/legal copy.
- Principal broker identity/title if it is required for publication; none is inferred.
- Formal privacy contact/role, production privacy notice, retention periods, service-provider/subprocessor disclosures, and consent-withdrawal process.
- Final complaints owner, response timing, record process, and accurate regulatory escalation wording.
- Formal accessibility policy, feedback process/owner, format-request process, and response timing.
- Approved booking provider URL; booking remains disabled and phone/contact are the honest current actions.
- Approved vector logo and font licences, plus licence/usage approval for the generated photography or replacement source assets.
- Owner visual approval at desktop, tablet, and 320 CSS pixels; browser visual regression and manual WCAG 2.1 AA review.
- Production hosting/origin, R2, hosted Supabase, monitoring, backup/restore, incident response, security/access review, and other Phase 1F operations.

## Deferred Phase 1B–1F work

- **1B:** lead notifications/queue, consent withdrawal, approved booking integration, and any approved agent/source attribution UX.
- **1C:** real recruitment postings, candidate identity/registration, applications, private uploads, and status.
- **1D:** review, decisions, onboarding plans/tasks, controlled documents, acknowledgements, and activation gates.
- **1E:** agent-profile administration, approval, published queries, safe attribution, suspension/archive behavior, and public detail pages.
- **1F:** production integration/operations, legal/privacy/compliance approval, accessibility and security audits, backup/restore, monitoring, pilot, and launch approval.
