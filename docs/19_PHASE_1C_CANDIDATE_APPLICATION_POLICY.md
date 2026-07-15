# Phase 1C Candidate Application Policy

**Approval date:** 2026-07-15<br>
**Status:** Approved product policy for Phase 1C engineering<br>
**Privacy disclosure version:** `candidate-privacy-disclosure-2026-07-15-v1`

This document is the complete Phase 1C product decision for the candidate questionnaire, application cardinality, candidate-uploaded document categories, candidate privacy disclosure, and candidate MFA. Engineering must implement these allow-lists and must not add questions or document categories without a later approved change.

This policy does not introduce regulatory suitability, licensing, background-check, government-identity, identity-document, or financial questions or document requirements.

## 1. Candidate application questionnaire

### General validation rules

- Trim leading and trailing whitespace from text. A required text value must contain at least one non-whitespace character.
- Reject control characters other than line breaks in multiline fields.
- Lengths are Unicode character counts after normalization and trimming.
- Dates use ISO `YYYY-MM-DD`; months use ISO `YYYY-MM`.
- Email comparison is case-insensitive. The account email is supplied by the verified identity provider and is not typed into the questionnaire.
- Phone input may contain spaces, parentheses, hyphens, and a leading `+`; store its normalized E.164 form of `+` followed by 8–15 digits.
- Country uses ISO 3166-1 alpha-2 codes. No province, territory, or country eligibility is inferred from an address.
- Repeatable-entry limits are enforced by the server.
- No questionnaire value may contain attachments or rich text. Multiline fields are plain text.

### Section A — Opportunity

| Field/code                  | Candidate label or source           |             Required? | Length/format                                          | Draft editability             |
| --------------------------- | ----------------------------------- | --------------------: | ------------------------------------------------------ | ----------------------------- |
| `recruitment_posting_id`    | Posting selected by the candidate   |              Required | Server-validated UUID of a currently published posting | No after the draft is created |
| `recruitment_posting_title` | Display-only posting title snapshot | Required system value | 1–160 characters; copied by the server                 | Never candidate-editable      |

A draft can be started only from a published posting. Closing or archiving a posting does not erase the posting snapshot from an existing application.

### Section B — Contact information

| Field/code                 | Candidate label          |              Required? | Length/format                                                                   | Draft editability                                                  |
| -------------------------- | ------------------------ | ---------------------: | ------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `given_name`               | First/given name         |               Required | 1–70 characters; single-line plain text                                         | Yes                                                                |
| `family_name`              | Last/family name         |               Required | 1–70 characters; single-line plain text                                         | Yes                                                                |
| `preferred_name`           | Preferred name           |               Optional | 0–70 characters; single-line plain text                                         | Yes                                                                |
| `email`                    | Email                    | Required account value | Valid email, maximum 254 characters; verified identity-provider email           | No; changed only through the identity provider and re-verification |
| `phone`                    | Phone number             |               Required | Candidate input maximum 32 characters; normalized to E.164 `+` plus 8–15 digits | Yes                                                                |
| `city`                     | City                     |               Required | 1–100 characters; single-line plain text                                        | Yes                                                                |
| `region`                   | Province/state/region    |               Optional | 0–100 characters; single-line plain text                                        | Yes                                                                |
| `country_code`             | Country                  |               Required | ISO 3166-1 alpha-2 value                                                        | Yes                                                                |
| `preferred_contact_method` | Preferred contact method |               Required | One of `email`, `phone`, `no_preference`                                        | Yes                                                                |

### Section C — Application details

| Field/code            | Candidate label                                   | Required? | Length/format                                                                                                          | Draft editability |
| --------------------- | ------------------------------------------------- | --------: | ---------------------------------------------------------------------------------------------------------------------- | ----------------- |
| `available_from`      | Earliest available start date                     |  Optional | ISO date `YYYY-MM-DD`; must be a real date                                                                             | Yes               |
| `referral_source`     | How did you hear about this opportunity?          |  Optional | One of `keeper_website`, `search`, `social_media`, `employee_or_agent_referral`, `event`, `other`, `prefer_not_to_say` | Yes               |
| `referral_detail`     | Referral details                                  |  Optional | 0–120 characters; single-line plain text; allowed only when source is `employee_or_agent_referral` or `other`          | Yes               |
| `interest_statement`  | Why are you interested in this opportunity?       |  Required | 100–2,000 characters; multiline plain text                                                                             | Yes               |
| `relevant_experience` | Briefly describe experience you consider relevant |  Optional | 0–2,000 characters; multiline plain text                                                                               | Yes               |

The two narrative prompts are general recruitment prompts. They must not be expanded into regulatory suitability, licensing, background, identity, or financial screening.

### Section D — Employment history

The section is optional. A candidate may provide zero to five entries. If an entry is started, `employer_name`, `role_title`, `start_month`, and `currently_employed` are required for that entry.

| Field/code                        | Candidate label                |   Required? | Length/format                                                                                                       | Draft editability |
| --------------------------------- | ------------------------------ | ----------: | ------------------------------------------------------------------------------------------------------------------- | ----------------- |
| `employment[].employer_name`      | Employer/organization          | Conditional | 1–160 characters; single-line plain text                                                                            | Yes               |
| `employment[].role_title`         | Role/title                     | Conditional | 1–160 characters; single-line plain text                                                                            | Yes               |
| `employment[].start_month`        | Start month                    | Conditional | ISO month `YYYY-MM`                                                                                                 | Yes               |
| `employment[].currently_employed` | I currently work here          | Conditional | Boolean                                                                                                             | Yes               |
| `employment[].end_month`          | End month                      | Conditional | ISO month `YYYY-MM`; required and not earlier than start month when `currently_employed` is false; absent when true | Yes               |
| `employment[].summary`            | Responsibilities or highlights |    Optional | 0–1,000 characters; multiline plain text                                                                            | Yes               |

### Section E — Education and training

The section is optional. A candidate may provide zero to three entries. This records candidate-chosen general education or training only; it does not request licence numbers, licence status, regulatory authorization, or proof. If an entry is started, `institution_name` and `program_name` are required for that entry.

| Field/code                     | Candidate label      |   Required? | Length/format                                       | Draft editability |
| ------------------------------ | -------------------- | ----------: | --------------------------------------------------- | ----------------- |
| `education[].institution_name` | Institution/provider | Conditional | 1–160 characters; single-line plain text            | Yes               |
| `education[].program_name`     | Program/course       | Conditional | 1–160 characters; single-line plain text            | Yes               |
| `education[].completion_year`  | Completion year      |    Optional | Four digits; 1900 through the current calendar year | Yes               |

### Section F — Privacy and declaration

| Field/code                       | Candidate label                                                                        |               Required? | Length/format                                                         | Draft editability                                                  |
| -------------------------------- | -------------------------------------------------------------------------------------- | ----------------------: | --------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `privacy_acknowledged`           | I have read the candidate privacy disclosure                                           | Required for submission | Boolean; must be `true` at submission                                 | Yes while draft; server records the approved version at submission |
| `information_accuracy_confirmed` | I confirm that the information I am submitting is accurate to the best of my knowledge | Required for submission | Boolean; must be `true` at submission                                 | Yes while draft                                                    |
| `privacy_disclosure_version`     | Disclosure version                                                                     |   Required system value | Exact server-owned value `candidate-privacy-disclosure-2026-07-15-v1` | Never candidate-editable                                           |

The accuracy confirmation is not an electronic signature, licence attestation, background consent, identity verification, or regulatory suitability declaration.

### Allowed free-text fields

The only candidate-entered free-form text values are:

- structured, single-line text: `given_name`, `family_name`, `preferred_name`, `phone`, `city`, `region`, `referral_detail`, `employment[].employer_name`, `employment[].role_title`, `education[].institution_name`, and `education[].program_name`;
- prose, multiline text: `interest_statement`, `relevant_experience`, and `employment[].summary`.

No generic “additional information,” “other comments,” internal-note, or document-description field is permitted. Each prose field must display an adjacent warning not to provide government identification numbers or documents, banking or financial information, health information, passwords, background-check information, licence numbers, or other information not requested by the prompt.

### Sections required for submission

A candidate may save an incomplete draft. Submission requires:

1. Section A — Opportunity;
2. Section B — Contact information;
3. Section C — Application details, with `interest_statement` complete; and
4. Section F — Privacy and declaration.

Sections D and E are optional. Documents are optional and are not a submission gate.

### Draft and post-submission edits

- While state is `draft`, the candidate may edit every candidate-entered questionnaire field identified as editable above, add/remove repeatable entries within their limits, and add or remove their uploaded documents.
- The candidate cannot change the posting, verified account email, server-owned posting-title snapshot, disclosure version, application identifiers, revision, timestamps, or lifecycle state.
- Submission creates an immutable application revision and records the exact disclosure version and acknowledgement time.
- After submission, questionnaire fields are read-only. A later information-request/reopen workflow may create a new controlled revision or response; it must not overwrite the submitted revision.
- Post-submission document uploads follow the separate append-only document rules below and do not alter the submitted questionnaire revision.

## 2. Candidate/application cardinality policy

- A candidate may have more than one application.
- Every application is posting-specific; `recruitment_posting_id` is mandatory for Phase 1C applications.
- Multiple concurrent applications are allowed, but a candidate may have only one nonterminal application for the same posting at a time.
- Candidate lifecycle and decisions are application-specific when multiple applications exist. A decision on one application must not silently decide another.
- A withdrawn or declined candidate may apply to a different published posting immediately.
- A withdrawn or declined candidate may reapply to the same posting only while it is published and only by creating a new application attempt. The prior submitted revision, status history, and documents remain distinct and immutable; they are never reset or overwritten.
- A candidate who withdraws retains read-only portal access to their submitted application and candidate-uploaded documents while the account and records remain under the approved retention policy. Quarantined, rejected-for-security, deleted-under-policy, or access-restricted objects are not downloadable. Withdrawal ends editing and new uploads for that application.
- Decline also ends editing and new uploads. Candidate-visible decline status/messages remain available while the account and records are retained.

The data model must therefore distinguish application identity/attempt and application-level lifecycle. A single candidate-wide status is not sufficient to represent concurrent applications.

## 3. Approved Phase 1C candidate document categories

No candidate document is required for submission in Phase 1C.

| Category     | Code           | Required? | Extensions              | Exact allowed MIME types                                                                                           |          Maximum per file | Upload window                                                               |
| ------------ | -------------- | --------: | ----------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------: | --------------------------------------------------------------------------- |
| Résumé/CV    | `resume`       |  Optional | `.pdf`, `.doc`, `.docx` | `application/pdf`; `application/msword`; `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 10 MiB (10,485,760 bytes) | Before submission and after submission while the application remains active |
| Cover letter | `cover_letter` |  Optional | `.pdf`, `.doc`, `.docx` | `application/pdf`; `application/msword`; `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | 10 MiB (10,485,760 bytes) | Before submission and after submission while the application remains active |

Document rules:

- The candidate must select a category; there is no `other` category.
- Extension, declared MIME type, and detected file signature must agree. Renaming a file does not make it acceptable.
- A candidate may retain at most five files in each category per application attempt.
- Before submission, candidates may remove their own uploads. After submission, uploads are append-only: a newer file may be marked current, but earlier metadata and audit evidence are retained and the submitted record is not silently replaced.
- After-submission upload is allowed only for nonterminal application states and requires AAL2. It ends on withdrawal or decline.
- Files remain private, quarantined until the production malware-scanning control accepts them, and inaccessible through public object URLs.
- Phase 1C must not add identity documents, background checks, credit reports, financial records, licensing evidence, suitability evidence, or a generic “other” upload category.

## 4. Approved candidate privacy disclosure

### Immutable identifier

`candidate-privacy-disclosure-2026-07-15-v1`

The identifier and exact disclosure text are server-owned. Editing the wording requires a new immutable identifier; existing submission records keep the version they acknowledged.

### Candidate-facing disclosure text

> **Candidate privacy disclosure**
>
> Keeper Financial Inc. collects candidate information to create and administer your account, receive and review applications for the opportunities you select, communicate with you about those applications, protect the portal, maintain application and access records, and operate the recruitment process.
>
> We collect your verified account email and authentication/security metadata; the contact details you provide; the posting and application details you select; your availability, referral source, candidate statements, employment history, and education or training entries; any résumé or cover letter you choose to upload and its file metadata; privacy acknowledgements; and application status, candidate-visible communications, history, and audit records. Phase 1C does not ask you for government identity documents or numbers, background-check information, licence information, or financial information.
>
> You can access your own candidate record. Within Keeper Financial, access is limited to authorized brokerage administrators and recruitment reviewers who need the information for the recruitment process, security, support, or records administration. Internal notes are not shown to candidates. Service providers that host or support identity, application, database, private file-storage, security, monitoring, or communications functions may process information only to provide those services under Keeper Financial’s direction and applicable safeguards. Candidate information is not provided to service providers for their own independent marketing.
>
> Candidate drafts, submitted applications, uploaded documents, acknowledgement records, and security/audit records are retained under Keeper Financial’s approved, policy-controlled retention categories for only as long as reasonably needed for recruitment, records administration, security, dispute handling, and applicable obligations. Retention may differ for abandoned drafts, withdrawn or declined applications, active applications, documents, and security or audit records. Records are deleted or de-identified when the applicable approved policy permits, subject to a documented legal or security hold. This notice does not promise an unsupported fixed legal retention period.
>
> Required fields are needed to identify and contact you within this recruitment process, associate the application with the selected opportunity, review the application, and record that this disclosure was shown. If you omit required information or do not acknowledge this disclosure, you may save a draft but cannot submit the application. Optional answers and optional documents may be omitted without preventing submission, although reviewers will not have information you choose not to provide.
>
> For privacy questions or requests, contact **support@keeperfinancial.ca**. Do not email sensitive documents; use the authenticated portal for permitted uploads.
>
> **Version:** `candidate-privacy-disclosure-2026-07-15-v1`

The disclosure must be displayed before submission and remain available from the candidate portal. Submission records the immutable version and timestamp; the client cannot select or override either.

## 5. Candidate MFA policy

Verified email and an active local candidate/application relationship remain required for all candidate portal access. AAL2 requirements are:

| Candidate action                                        | AAL2 required? |
| ------------------------------------------------------- | -------------: |
| General candidate portal access                         |             No |
| Save or update an application draft                     |             No |
| Submit an application                                   |             No |
| Upload a candidate document, before or after submission |            Yes |
| View or download any restricted document                |            Yes |

Additional rules:

- An AAL1 candidate may view their questionnaire and candidate-visible status/messages, subject to ownership and lifecycle checks.
- A document-upload, restricted-document listing that exposes sensitive metadata, or document-view/download action must step up to AAL2 and re-run server-side ownership, relationship, lifecycle, quarantine, and authorization checks.
- A short-lived URL does not replace AAL2 or authorization. It may be issued only after the checks succeed.
- AAL2 must be asserted by the managed identity provider; the application must not accept a caller-supplied MFA flag.
- Brokerage administrators remain subject to the existing mandatory nonlocal AAL2 policy.
