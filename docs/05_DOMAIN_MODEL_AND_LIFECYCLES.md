# Domain Model and Lifecycles

## Core entities

### User

Local application account mapped to an identity provider subject.

### Candidate

Represents a person’s local brokerage recruitment relationship. Its status is
used for relationship-level access denial such as suspension or offboarding;
posting-specific review decisions belong to `CandidateApplication`.

### CandidateApplication

Versioned or controlled application content associated with a candidate and a required recruitment posting. It is the authority for posting-specific review and onboarding-entry lifecycle state. A candidate may have multiple concurrent applications, but only one nonterminal application per posting. A withdrawn or declined reapplication is a distinct immutable attempt, not a reset of the prior record. See `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`.

### RecruitmentPosting

Public or internal opportunity with publication lifecycle.

### OnboardingPlan

Reusable template containing ordered tasks. It may be edited only while no
assignment references it; first use makes the plan and task set permanently
immutable.

### CandidateOnboardingTask

Assigned task instance linked to an exact application-bound onboarding
assignment, with status, evidence, reviewer, and due date.

### CandidateOnboardingAssignment

An immutable generation linking the selected `CandidateApplication`, candidate,
active `OnboardingPlan`, assigned tasks, and exact controlled-document versions.
Only one assignment for an application may be active. Historical generations
remain available as superseded evidence.

### ControlledDocument

Logical policy, agreement, guide, or form.

### DocumentVersion

Immutable issued version of a controlled document.

### CandidateDocument

Candidate-uploaded or generated document metadata and private storage reference.

### PolicyAcknowledgement

Evidence that a candidate acknowledged a specific eligible document version
through the candidate's current application-bound onboarding assignment. It is
not a signature.

### ProgrammaticGate and GateEvidenceEvent

An exact-assignment gate projection plus append-oriented manual evidence and
reopen history. Only background check, FSRA authorization, and system
provisioning accept manual evidence. Policy acknowledgement and executed
agreements are derived from assignment-specific records and cannot be manually
asserted or reopened.

### CandidateEsignEnvelope

A bounded Documenso envelope reference linked to one exact assignment.
Provider-authoritative completion may satisfy executed agreements. A rejected
envelope may be replaced without deleting predecessor history.

### AgentProfile

Brokerage-controlled public profile with separate draft and publication state.
The first publication permanently locks and reserves its public slug, including
while the profile is later non-public.

### LeadInquiry

Minimal client contact-first inquiry. It is not a mortgage application.

### ConsentRecord

Versioned evidence of a defined consent or acknowledgement.

### AuditEvent

Append-oriented evidence of sensitive activity.

## Candidate lifecycle

```text
prospect
  → application_started
  → application_submitted
  → under_review
  → more_information_required
  → under_review
  → interview
  → conditionally_selected
  → onboarding_in_progress
  → pending_fsra_authorization
  → pending_system_provisioning
  → active
  → suspended
  → offboarding
  → offboarded
```

Terminal or alternate states:

```text
application_started → withdrawn
application_submitted → withdrawn
under_review → declined
more_information_required → declined
interview → declined
conditionally_selected → declined
```

## Lifecycle rules

- Candidate cannot self-select.
- Candidate cannot self-activate.
- Recruitment decisions and lifecycle state are application-specific when a candidate has multiple applications.
- Review and decision operations lock and transition the selected application attempt; candidate-wide relationship state is not a substitute for application state.
- Withdrawal or decline of one application must not silently transition another application.
- Invalid transitions must fail.
- Status reason is mandatory for decline, suspension, override, and offboarding.
- Activation must check all configured mandatory gates.
- FSRA authorization is a recorded administrative verification unless a later authoritative integration is approved.
- System provisioning is a tracked task until a real vendor integration exists.
- Onboarding assignment requires the selected application to be `conditionally_selected` and the selected plan to be active.
- Every assignment snapshots exact currently issued, non-superseded controlled-document versions. A required assigned version that later becomes superseded remains readiness-blocking unless its exact version was already acknowledged; it cannot be acknowledged after becoming ineligible.
- `activation_ready` is a calculation over the current application-bound assignment, required tasks, exact assigned policy acknowledgements, and configured gates. It does not activate an agent.
- Gate, acknowledgement, and e-sign satisfaction never crosses assignment generations. Administrators can satisfy/reopen only the three manual gates; the two derived gates are recalculated from exact-assignment evidence.
- Only a completed Keeper-issued envelope with validated template/external-ID/recipient provenance satisfies `executed_agreements`; manual/recovery links, rejected envelopes, and replaced predecessors do not. Provider refresh is authoritative and failures leave readiness unsatisfied.
- One owner-configured Documenso agreement template may be instantiated and distributed only for the exact active assignment's application-linked authoritative user. The candidate recipient cannot be overridden in Keeper. A manual provider-envelope link may preserve recovery/history and reconcile status, but it has no issuance-validated signing URL and cannot satisfy readiness or completion. Rejected, voided, or recovery-only current envelopes may be superseded by the same bounded issuance operation only after the provider returns a fully validated replacement; provider failure leaves the predecessor current.
- Final onboarding completion is an explicit administrator/AAL2 operation regardless of any broader admin-MFA environment toggle, never an automatic consequence of a signing link or browser response. It row-locks and revalidates the exact active assignment, submitted `onboarding_in_progress` application, activatable nonterminal candidate relationship, active user, current Keeper-issued envelope, and existing `agent` role before changing state.
- Successful completion is one atomic, idempotent transition: assignment `active → completed`, exact application and candidate relationship → `active`, and one existing `agent` role grant to the same active user. The candidate role and historical onboarding access remain; status history and safe audit evidence are appended once.
- A completed assignment is read-only. It remains available to candidate and administrator projections as completed history, but its tasks, gates, acknowledgements, and e-sign evidence cannot be mutated through active-assignment operations.
- Completion does not create or publish an `AgentProfile`; it only makes the user eligible for the existing administrator agent-profile flow.

## Agent-profile lifecycle

```text
draft
  → pending_approval
  → published
  → suspended
  → published
  → archived
```

Rules:

- Draft is private.
- Pending approval is private.
- Published requires authorized approval.
- Suspended is not public.
- Archived is not public and cannot be republished without an explicit restore workflow.
- The slug is selected before first publication, server-checked for availability, and becomes immutable and permanently reserved at first publication. Suspension, archive, or other unpublishing does not release it.

## Recruitment-posting lifecycle

```text
draft → published → closed → archived
```

Only `published` postings are public.

## Document lifecycle

Logical document:

```text
draft version → issued version → superseded
```

Candidate task status may include:

```text
required
available
viewed
acknowledged
sent_for_signature
signed
uploaded
accepted
rejected
expired
superseded
```

Rules:

- Issued document versions are immutable.
- A new revision creates a new version.
- Acceptance or acknowledgement must reference the exact version.
- Rejected uploads retain evidence of rejection and replacement.
- Deleted object data must not silently erase required audit metadata.

## Step 9 schema-retention controls

- An onboarding task template referenced by a candidate task cannot be hard
  deleted. Plans and templates use their application lifecycle, and PostgreSQL
  `ON DELETE RESTRICT` protects completed or reviewed candidate-task evidence.
- `reviewed_by_user_id` remains nullable for tasks that have not been reviewed.
  Once populated, the referenced user cannot be hard deleted; operator
  offboarding uses user deactivation so reviewer attribution remains intact.
- A document version referenced by a policy acknowledgement cannot be deleted.
  The acknowledgement retains an explicit `ON DELETE RESTRICT` link to the
  exact immutable version accepted.
- Candidate e-sign envelopes, information requests, and programmatic gates keep
  their candidate-first creation-order indexes. A candidate-only index is not
  added when that left prefix already supports the query.
- Assignment generation uniqueness on
  `(candidate_id, onboarding_plan_id, generation)` supplies the same PostgreSQL
  btree needed for candidate/plan lookup and generation ordering; a second
  non-unique index on those exact columns is intentionally absent.

## Lead lifecycle

Initial minimal lifecycle:

```text
new → assigned → contacted → closed
```

This is not a full CRM lifecycle. It exists only to prevent website inquiries from being lost.

## 2026-07-18 browser-completion clarification

An administrator information request is bound to one exact
`CandidateApplication` attempt. It is permitted only while that application is
`under_review` or `interview`; it transitions that same attempt to
`more_information_required` and does not mutate another posting or attempt. A
newly `application_submitted` attempt must first enter `under_review`.

No onboarding assignment is a normal candidate state, not an authorization
failure. It produces `available=false`, an empty dashboard, and
`activation_ready=false`. It creates no tasks, gates, document assignments, or
agent activation.
