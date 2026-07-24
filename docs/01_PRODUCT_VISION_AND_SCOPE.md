# Product Vision and Scope

## Vision

Create a premium, trustworthy digital presence for Keeper Financial while giving the brokerage a controlled, auditable way to recruit, assess, onboard, support, and publicly represent mortgage agents.

## Business outcomes

- Convert website visitors into either conversations or secure mortgage applications.
- Reduce friction for prospective agents.
- Give the principal broker and administrators visibility into candidate progress.
- Standardize onboarding.
- Reduce document chasing and version confusion.
- Maintain consistent, approved public agent branding.
- Make Keeper the secure system of record for borrower application intake and supporting documents.
- Preserve a future integration boundary without requiring Filogix or another provider in the MVP.
- Avoid expanding intake into automated underwriting, lender submission, deal compliance, or a full client CRM.

## Phase 1 personas

### Mortgage prospect

Wants to:

- Understand Keeper Financial.
- Learn about mortgage services.
- Speak with someone before applying.
- Start a secure full application.
- Find or select an agent.
- Submit supporting documents and versioned privacy/credit-use consent securely.

### Agent candidate

Wants to:

- Understand the brokerage opportunity.
- Review available postings.
- Create an account.
- Save and submit an application.
- Upload required candidate documents.
- Respond to requests.
- See status.
- Complete onboarding when selected.

### Active mortgage agent

Wants to:

- Maintain approved public profile information.
- Access onboarding and policy records.
- Receive brokerage resources later.
- Direct clients to an attributed application path.
- Review only borrower applications assigned to the agent through an authenticated AAL2 portal.

### Brokerage administrator

Wants to:

- Publish recruitment postings.
- Review candidate applications.
- Request information.
- Record decisions.
- Assign onboarding plans.
- Track documents, acknowledgements, and tasks.
- Approve agent profiles.
- Suspend or archive access.
- Export an auditable candidate/onboarding record.

### Principal broker or compliance reviewer

Wants to:

- See evidence of review and approval.
- Confirm that required training and policies were completed.
- Control public advertising and agent representation.
- Review exceptions.
- Ensure only authorized people become active.

## In scope

### Public website

- Home and core service pages.
- Mortgage information pages.
- `Get Started` page.
- Minimal contact-first inquiry.
- Keeper-native borrower application at `apply.keeperfinancial.ca`.
- Public agent directory and profiles.
- Careers and recruitment postings.
- Privacy, complaints, accessibility, and contact pages.
- Responsive and accessible implementation.
- Search and social metadata.

### Borrower application

- Accountless capability-bound same-browser draft for one primary borrower and at most one co-borrower.
- Mortgage request, SIN, employment/income, property, asset/liability, notes, privacy/credit-use consent, and supporting-document intake.
- Application-level encryption, private MinIO, fail-closed ClamAV, immutable submitted snapshots, seven-year retention, and legal holds.
- Assigned-agent and administrator review with server-side authorization and AAL2.

### Candidate portal

- Registration and verified sign-in.
- Application draft and submission.
- Supporting document upload.
- Status display.
- Request-for-information response.
- Onboarding checklist.
- Controlled document access.
- Policy acknowledgement.
- Executed-document upload or external e-signature status.
- Completion tracking.

### Brokerage administration

- Candidate pipeline.
- Review notes.
- Status transitions.
- Recruitment posting administration.
- Onboarding templates and assignments.
- Document/version management.
- Agent-profile approval.
- Audit events.
- Basic exports.

## Deferred

- Client CRM replacement.
- Filogix export/import or API integration.
- Credit-bureau connectivity, automated underwriting, lender submission, and deal-compliance workflow.
- Borrower accounts, cross-device resume, post-submission borrower portal, and borrower MFA.
- Lead scoring.
- Full email/SMS marketing automation.
- Renewal campaigns.
- Referral partner portal.
- Custom agent microsites.
- Commission calculations.
- Payroll.
- Full learning-management system.
- Automated vendor provisioning.
- Automated licensing validation.
- Advanced analytics.
- Multi-province logic.
