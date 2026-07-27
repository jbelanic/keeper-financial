import type { Metadata } from "next";
import { InteriorPageHeader } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";

const APPROVED_CONTENT = `Privacy Notice
Effective date: Jul 23, 2026

This notice describes how Keeper Financial Inc., operating as Keeper Financial, collects, uses, discloses and protects personal information through keeperfinancial.ca, its candidate portal and related communications.

Information we collect
Through the public contact form, we may collect your name, email address, telephone number, general mortgage objective, preferred contact method, selected agent and an optional non-sensitive message.

Through the candidate portal, we may collect account and security information, contact details, application answers, employment and education history, optional résumés and cover letters, application status and communications, interview and review records, onboarding task information, controlled-document acknowledgements, external-signing workflow references and other onboarding-status records.

The public contact form is not a full mortgage application. Do not send a SIN, detailed banking or credit information, tax records, identity documents or mortgage documents through a general contact form or general email.

How we use personal information
We may use personal information to:

respond to service inquiries;
communicate about mortgage services requested by you;
administer candidate accounts, applications, review and onboarding;
protect accounts, systems and records;
maintain consent, access, security and audit evidence;
meet approved legal, regulatory, records-management and dispute-handling requirements; and
send optional marketing communications only where an appropriate consent or other lawful basis has been established.
Required and optional information
Fields identified as required are needed to process the relevant inquiry or candidate application. Optional fields may be left blank. If required information or a required acknowledgement is not provided, we may be unable to process or submit the request.

Service providers and disclosure
We may use service providers to support identity, hosting, database, private file storage, security, monitoring, communications, mortgage applications and external signing. Before publication, Keeper Financial must confirm the approved provider categories, subprocessors, processing locations and contractual safeguards.

We do not sell personal information or permit service providers to use candidate information for their own independent marketing. 

Mortgage applications and external services
A complete mortgage application is handled through Filogix. When you follow an external link, the destination’s privacy terms and security practices may also apply. Review those materials before submitting detailed information.

Cookies and similar technologies
The signed-in portal uses cookies required to establish and protect account sessions. The public website does not currently use analytics, advertising or preference cookies. If non-essential technologies are introduced, this notice and any required choices must be updated before deployment.

Safeguards
Keeper Financial uses administrative, technical and physical safeguards appropriate to the information and the service. No method of transmission or storage can be guaranteed to be completely secure.

Retention
Keeper Financial retains personal information according to approved record categories and schedules. Retention may differ for public inquiries, consent records, candidate drafts, submitted or withdrawn applications, documents, onboarding records and security or audit records.

Before publication, insert approved retention principles or link to the approved schedule. Do not insert fixed periods or legal-hold wording until approved by legal and privacy reviewers.

Access, correction, export, deletion and consent questions
You may contact Keeper Financial to ask about personal information or request access, correction, export or deletion. Requests are subject to identity verification and any applicable legal, regulatory, security and records-management requirements.

To withdraw optional marketing consent, use the unsubscribe method in the communication or contact support@keeperfinancial.ca. Withdrawal does not affect service communications needed to respond to an inquiry or administer an application.

Contact
Privacy contact: Privacy Officer Email: privacy@keeperfinancial.ca 

Changes to this notice
We may update this notice when our practices or requirements change. The effective date above identifies the version currently published.`;

// Process the approved content to remove the first three lines (title, effective date, blank line)
const lines = APPROVED_CONTENT.split("\n");
const articleContentLines = lines.slice(3); // Remove "Privacy Notice", "Effective date: Jul 23, 2026", and the blank line
const articleContent = articleContentLines.join("\n");

const sectionHeaders = [
  "Information we collect",
  "How we use personal information",
  "Required and optional information",
  "Service providers and disclosure",
  "Mortgage applications and external services",
  "Cookies and similar technologies",
  "Safeguards",
  "Retention",
  "Access, correction, export, deletion and consent questions",
  "Contact",
  "Changes to this notice",
];

// Split the article content into blocks separated by one or more blank lines
const blocks = articleContent.trim().split(/\s*\n\s*\n/);

export const metadata: Metadata = createPageMetadata({
  title: "Privacy Notice",
  description:
    "This notice describes how Keeper Financial Inc., operating as Keeper Financial, collects, uses, discloses and protects personal information through keeperfinancial.ca, its candidate portal and related communications.",
  path: "/privacy",
});

export default function PrivacyPage() {
  return (
    <div className="container policy-page">
      <InteriorPageHeader
        title="Privacy Notice"
        description="Effective date: Jul 23, 2026"
      />
      <article className="policy-content">
        {blocks.map((block, index) => {
          const trimmed = block.trim();
          if (sectionHeaders.includes(trimmed)) {
            return <h2 key={index}>{trimmed}</h2>;
          } else {
            // Convert newlines within the block to <br> for line breaks
            const contentWithBreaks = trimmed.replace(/\n/g, "<br>");
            return (
              <p
                dangerouslySetInnerHTML={{ __html: contentWithBreaks }}
                key={index}
              />
            );
          }
        })}
      </article>
    </div>
  );
}
