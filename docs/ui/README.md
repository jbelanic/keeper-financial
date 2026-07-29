# Approved Mockup Incorporation

Reference images live in `docs/ui/reference`. They are visual direction, not production claims or executable specifications.

Phase 1A implementation:

1. Approved paper/ink/gold values are mapped into `packages/ui/src/tokens.css`; reusable primitives and public compositions live in `packages/ui` and `apps/web/lib/public-components.tsx`.
2. The public navigation, mobile `details`/`summary` menu, footer, hero, cards, forms, disclosures, breadcrumbs, status states, and CTA patterns adapt desktop intent for semantics, keyboard focus, reduced motion, and narrow-screen reflow.
3. No mockup rating, rate, award, testimonial, example person, agent licence, NMLS value, production/pipeline metric, or CRM capability is reproduced as a public claim. Recruitment claims approved by the owner on 2026-07-29 are recorded in `docs/09_DECISIONS_ASSUMPTIONS_AND_OPEN_QUESTIONS.md` and are not sourced from the mockup.
4. The approved target keeps the contact-first and Keeper-native application paths visually equal; after the borrower workflow is implemented and accepted, the full-application action must enter only `apply.keeperfinancial.ca`, while each path preserves its own data-minimization, consent, abuse, and security boundary. Phase A does not implement this target, and current code still contains the legacy external redirect.
5. The agent-profile mockup is used only for shared card/icon/spacing direction. No CRM dashboard, credit-bureau, automated underwriting/approval, lender-submission, or deal-compliance functionality is implemented.

## Controlled raster assets

Both assets were produced with the configured image-generation workflow. The home image remains the Phase 1A output. The recruitment image was replaced on 2026-07-29 at the owner's request after the original generated scene was judged too placeholder-like. They are new photography-only outputs, not screenshot crops, and include no embedded Keeper UI, logo, readable text, claims, documents, or sample data. Next.js handles responsive output optimization; each source has an explicit crop-safe `next/image` container.

| Project asset | Approved reference | Purpose | Source dimensions | SHA-256 |
|---|---|---|---|---|
| `apps/web/public/images/home-conversation.png` | `docs/ui/reference/keeper-home-desktop.png` | Home split hero; adult couple in a warm living room | 1536 × 1024 | `ddf9374e9b87ece6ce31f94950abab39aca05a4fb76eafe6c118bac13549d08d` |
| `apps/web/public/images/recruitment-team.png` | `docs/ui/reference/keeper-recruitment-desktop.png` | Recruitment hero/band; four fictional professionals collaborating around a table | 1024 × 576 | `96efe963f031b341425d2c1da77ebd84b9fc65c697106d1a36cbde4aada94c74` |

Generation prompts specified premium natural editorial scenes, realistic textures, and explicit prohibitions on text, logos, readable documents, UI, financial figures, badges, claims, watermarks, or identifiable people from the references. The 2026-07-29 recruitment replacement uses a centred, crop-safe working scene rather than the original asset's large blank wall. It must not be represented as Keeper staff or premises.

## Owner approvals completed — 2026-07-29

- The owner approved production use of the generated raster assets.
- On 2026-07-29, the owner authorized replacing the recruitment image with a newly generated working scene after identifying the original as placeholder-like. Final visual acceptance of the replacement remains an owner decision.
- The owner approved the current font selection and accessible CSS/text lockup. A standalone vector logo is not required for the recruitment refresh.
- The owner approved the recruitment visual direction at desktop, tablet, and 320 CSS pixels.
- The owner removed the approval blocker associated with the stated visual-regression, accessibility, and manual WCAG review item. This approval does not represent evidence that a particular automated suite or specialist manual review was run; implementation reports must continue to state the checks actually completed.

The Phase 0 tokens use the mockups’ restrained paper/ink/gold direction and serif-display/sans-body structure without claiming final brand fidelity.
