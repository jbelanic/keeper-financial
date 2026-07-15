# Domain Model and Lifecycles

## Core entities

### User

Local application account mapped to an identity provider subject.

### Candidate

Represents a person’s relationship with the brokerage recruitment process.

### CandidateApplication

Versioned or controlled application content associated with a candidate and a required recruitment posting. A candidate may have multiple concurrent applications, but only one nonterminal application per posting. A withdrawn or declined reapplication is a distinct immutable attempt, not a reset of the prior record. See `docs/19_PHASE_1C_CANDIDATE_APPLICATION_POLICY.md`.

### RecruitmentPosting

Public or internal opportunity with publication lifecycle.

### OnboardingPlan

Reusable template containing ordered tasks.

### CandidateOnboardingTask

Assigned task instance with status, evidence, reviewer, and due date.

### ControlledDocument

Logical policy, agreement, guide, or form.

### DocumentVersion

Immutable issued version of a controlled document.

### CandidateDocument

Candidate-uploaded or generated document metadata and private storage reference.

### PolicyAcknowledgement

Evidence that a candidate or agent acknowledged a specific document version.

### AgentProfile

Brokerage-controlled public profile with separate draft and publication state.

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
- Withdrawal or decline of one application must not silently transition another application.
- Invalid transitions must fail.
- Status reason is mandatory for decline, suspension, override, and offboarding.
- Activation must check all configured mandatory gates.
- FSRA authorization is a recorded administrative verification unless a later authoritative integration is approved.
- System provisioning is a tracked task until a real vendor integration exists.

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

## Lead lifecycle

Initial minimal lifecycle:

```text
new → assigned → contacted → closed
```

This is not a full CRM lifecycle. It exists only to prevent website inquiries from being lost.
