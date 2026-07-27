# Agent Full-Application-Data Privacy-Boundary Approval

**Date:** 2026-07-27
**Owner decision:** Approved for the bounded agent-retrieval feature (`feat/agent-retrieval-minimal`)
**Status:** Authoritative for this phase only. Does not alter the borrower public/review privacy model elsewhere.

## Decision

The owner approves widening the **assigned-agent** internal review projection beyond the
existing masked shape so that an assigned, AAL2-verified, active agent can retrieve the
full submitted application needed to populate an external mortgage-origination system
(Filogix).

### Approved widening (agent view only)

For the exact assigned agent (enforced by `require_internal_agent_access`):
- Full unmasked SIN for primary and co-borrower (no longer masked).
- `assets`, `liabilities`, `subject_property`, `other_properties`, `additional_notes`.
- All other currently-returned fields unchanged.

### Hard constraints (must not change)

- The **administrator/AAL2 review console** and the **masked projection** used by
  administrators remain masked (SIN masked, no full financial detail). This approval
  applies ONLY to the exact assigned agent's own assigned application.
- Access remains gated by `require_internal_agent_access`: active + verified + AAL2 +
  `agent` role + active `Candidate` status + exact `assigned_agent_id` match.
- Every full-data/SIN retrieval by an agent is recorded in the audit trail with a
  safe reason code and actor identity.
- No new data class is introduced; only the existing stored encrypted payload is
  projected to the authorized agent.
- The public borrower capability never returns this data, before or after submission.

### Out of scope (still excluded)

- Full CRM, lead-assignment workflow, bulk export, marketing automation, independent
  agent portals/microsites (per `docs/26` Phase 1F exclusions).
- Automated underwriting/approval, lender submission, deal compliance, commissions.
- Webhooks, co-borrower collaboration invitations, post-submission borrower portal.
- Any change to the privacy boundary for administrators or any non-assigned principal.

## Rationale

Agents originate the client relationship and direct clients to complete the application.
To work the deal in Filogix they require the complete submitted data set, including SIN
and full financial detail, for the specific applications assigned to them. The existing
server authorization already scopes this to the exact assigned agent; this approval
authorizes the projection widening required to act on that authorization.

## Revocation

This approval is scoped to `feat/agent-retrieval-minimal`. A later owner decision may
narrow or reverse it; if reversed, the agent projection must revert to masked and omit
the full financial detail and unmasked SIN.
