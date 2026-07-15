from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class CandidatePrivacyDisclosure:
    version: str
    title: str
    paragraphs: tuple[str, ...]


CANDIDATE_PRIVACY_DISCLOSURE: Final = CandidatePrivacyDisclosure(
    version="candidate-privacy-disclosure-2026-07-15-v1",
    title="Candidate privacy disclosure",
    paragraphs=(
        "Keeper Financial Inc. collects candidate information to create and administer your "
        "account, receive and review applications for the opportunities you select, communicate "
        "with you about those applications, protect the portal, maintain application and access "
        "records, and operate the recruitment process.",
        "We collect your verified account email and authentication/security metadata; the contact "
        "details you provide; the posting and application details you select; your availability, "
        "referral source, candidate statements, employment history, and education or training "
        "entries; any résumé or cover letter you choose to upload and its file metadata; privacy "
        "acknowledgements; and application status, candidate-visible communications, history, and "
        "audit records. Phase 1C does not ask you for government identity documents or numbers, "
        "background-check information, licence information, or financial information.",
        "You can access your own candidate record. Within Keeper Financial, access is limited to "
        "authorized brokerage administrators and recruitment reviewers who need the information "
        "for the recruitment process, security, support, or records administration. Internal notes "
        "are not shown to candidates. Service providers that host or support identity, application, "
        "database, private file-storage, security, monitoring, or communications functions may "
        "process information only to provide those services under Keeper Financial\u2019s direction and "
        "applicable safeguards. Candidate information is not provided to service providers for "
        "their own independent marketing.",
        "Candidate drafts, submitted applications, uploaded documents, acknowledgement records, "
        "and security/audit records are retained under Keeper Financial\u2019s approved, policy-controlled "
        "retention categories for only as long as reasonably needed for recruitment, records "
        "administration, security, dispute handling, and applicable obligations. Retention may "
        "differ for abandoned drafts, withdrawn or declined applications, active applications, "
        "documents, and security or audit records. Records are deleted or de-identified when the "
        "applicable approved policy permits, subject to a documented legal or security hold. This "
        "notice does not promise an unsupported fixed legal retention period.",
        "Required fields are needed to identify and contact you within this recruitment process, "
        "associate the application with the selected opportunity, review the application, and record "
        "that this disclosure was shown. If you omit required information or do not acknowledge this "
        "disclosure, you may save a draft but cannot submit the application. Optional answers and "
        "optional documents may be omitted without preventing submission, although reviewers will "
        "not have information you choose not to provide.",
        "For privacy questions or requests, contact support@keeperfinancial.ca. Do not email sensitive "
        "documents; use the authenticated portal for permitted uploads.",
    ),
)
