# Approved Mockup Incorporation

Reference images live in `docs/ui/reference`. They are visual direction, not production claims or executable specifications.

For the approved UI pass:

1. Confirm image/font licensing, final navigation, approved copy, regulatory identity, and responsive intent with the owner.
2. Map approved values into `packages/ui/src/tokens.css`; do not scatter one-off brand constants through pages.
3. Extend primitives in `packages/ui` before composing page-specific patterns.
4. Adapt desktop-only interactions for keyboard, focus, semantics, 320 CSS-pixel reflow, zoom, reduced motion, and contrast.
5. Do not reproduce mockup claims such as ratings, lender counts, rates, licence numbers, production metrics, CRM capability, or testimonials without evidence and approval.
6. Add visual regression and accessibility tests at agreed viewport sizes.
7. Preserve the equal prominence of both `/apply` paths and the boundary against collecting borrower underwriting information.

The Phase 0 tokens use the mockups’ restrained paper/ink/gold direction and serif-display/sans-body structure without claiming final brand fidelity.
