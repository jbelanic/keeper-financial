# Approved Mockup Incorporation

Reference images live in `docs/ui/reference`. They are visual direction, not production claims or executable specifications.

Phase 1A implementation:

1. Approved paper/ink/gold values are mapped into `packages/ui/src/tokens.css`; reusable primitives and public compositions live in `packages/ui` and `apps/web/lib/public-components.tsx`.
2. The public navigation, mobile `details`/`summary` menu, footer, hero, cards, forms, disclosures, breadcrumbs, status states, and CTA patterns adapt desktop intent for semantics, keyboard focus, reduced motion, and narrow-screen reflow.
3. No mockup rating, lender count, rate, award, testimonial, example person, agent licence, NMLS value, compensation promise, production/pipeline metric, or CRM capability is reproduced as a public claim.
4. `/apply` keeps both paths visually equal and preserves the Phase 0 data-minimization, consent, abuse-control, and validated redirect boundary.
5. The agent-profile mockup is used only for shared card/icon/spacing direction. No CRM dashboard or mortgage-origination functionality is implemented.

## Phase 1A raster assets

Both assets were produced with the built-in `imagegen` workflow using the listed approved mockup only as a style/composition reference. They are new photography-only outputs, not screenshot crops, and include no embedded Keeper UI, logo, text, claims, documents, or sample data. Next.js handles responsive output optimization; each source has an explicit 1536 × 1024 aspect ratio and crop-safe `next/image` container.

| Project asset | Approved reference | Purpose | SHA-256 |
|---|---|---|---|
| `apps/web/public/images/home-conversation.png` | `docs/ui/reference/keeper-home-desktop.png` | Home split hero; adult couple in a warm living room | `ddf9374e9b87ece6ce31f94950abab39aca05a4fb76eafe6c118bac13549d08d` |
| `apps/web/public/images/recruitment-team.png` | `docs/ui/reference/keeper-recruitment-desktop.png` | Recruitment hero/band; three professionals in a modern office | `7ae431f6bf016020c28218e3cfc05c704d55a96437bf5551a1bd501853c41201` |

Generation prompts specified premium photorealistic-natural editorial scenes, right-weighted subjects with crop-safe negative space, warm ivory/oat/charcoal/brass palettes, realistic textures, and explicit prohibitions on text, logos, readable documents, UI, financial figures, badges, claims, watermarks, or identifiable people from the references.

## Approval still required

- Licence/usage approval for the generated raster assets or replacement source photography.
- Final font licensing and an approved standalone logo/vector asset if the CSS/text lockup is to be replaced.
- Owner visual approval at desktop, tablet, and 320 CSS pixels.
- Automated browser visual-regression/accessibility coverage and manual WCAG 2.1 AA review at agreed viewports.

The Phase 0 tokens use the mockups’ restrained paper/ink/gold direction and serif-display/sans-body structure without claiming final brand fidelity.
