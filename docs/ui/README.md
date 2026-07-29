# Approved Mockup Incorporation

Reference images live in `docs/ui/reference`. They are visual direction, not production claims or executable specifications.

Phase 1A implementation:

1. Approved paper/ink/gold values are mapped into `packages/ui/src/tokens.css`; reusable primitives and public compositions live in `packages/ui` and `apps/web/lib/public-components.tsx`.
2. The public navigation, mobile `details`/`summary` menu, footer, hero, cards, forms, disclosures, breadcrumbs, status states, and CTA patterns adapt desktop intent for semantics, keyboard focus, reduced motion, and narrow-screen reflow.
3. No mockup rating, rate, award, testimonial, example person, agent licence, NMLS value, production/pipeline metric, or CRM capability is reproduced as a public claim. Recruitment claims approved by the owner on 2026-07-29 are recorded in `docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md` and are not sourced from the mockup.
4. The approved target keeps the contact-first and Keeper-native application paths visually equal; after the borrower workflow is implemented and accepted, the full-application action must enter only `apply.keeperfinancial.ca`, while each path preserves its own data-minimization, consent, abuse, and security boundary. Phase A does not implement this target, and current code still contains the legacy external redirect.
5. The agent-profile mockup is used only for shared card/icon/spacing direction. No CRM dashboard, credit-bureau, automated underwriting/approval, lender-submission, or deal-compliance functionality is implemented.

## Phase 1A raster assets

Both assets were produced with the built-in `imagegen` workflow using the listed approved mockup only as a style/composition reference. They are new photography-only outputs, not screenshot crops, and include no embedded Keeper UI, logo, text, claims, documents, or sample data. Next.js handles responsive output optimization; each source has an explicit 1536 × 1024 aspect ratio and crop-safe `next/image` container.

| Project asset | Approved reference | Purpose | SHA-256 |
|---|---|---|---|
| `apps/web/public/images/home-conversation.png` | `docs/ui/reference/keeper-home-desktop.png` | Home split hero; adult couple in a warm living room | `ddf9374e9b87ece6ce31f94950abab39aca05a4fb76eafe6c118bac13549d08d` |
| `apps/web/public/images/recruitment-team.png` | `docs/ui/reference/keeper-recruitment-desktop.png` | Recruitment hero/band; three professionals in a modern office | `7ae431f6bf016020c28218e3cfc05c704d55a96437bf5551a1bd501853c41201` |

Generation prompts specified premium photorealistic-natural editorial scenes, right-weighted subjects with crop-safe negative space, warm ivory/oat/charcoal/brass palettes, realistic textures, and explicit prohibitions on text, logos, readable documents, UI, financial figures, badges, claims, watermarks, or identifiable people from the references.

## Owner approvals completed — 2026-07-29

- The owner approved production use of the generated raster assets.
- The owner approved the current font selection and accessible CSS/text lockup. A standalone vector logo is not required for the recruitment refresh.
- The owner approved the recruitment visual direction at desktop, tablet, and 320 CSS pixels.
- The owner removed the approval blocker associated with the stated visual-regression, accessibility, and manual WCAG review item. This approval does not represent evidence that a particular automated suite or specialist manual review was run; implementation reports must continue to state the checks actually completed.

The Phase 0 tokens use the mockups’ restrained paper/ink/gold direction and serif-display/sans-body structure without claiming final brand fidelity.
