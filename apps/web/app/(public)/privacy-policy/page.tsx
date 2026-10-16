import type { Metadata } from "next";
import { InteriorPageHeader } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";

const APPROVED_CONTENT = `Privacy Notice
Effective date: Oct 16, 2026

This notice describes how Keeper Financial Inc., operating as Keeper Financial, collects, uses, discloses and protects personal information through keeperfinancial.ca, the online mortgage application, the candidate portal and related communications.

Information we collect
Through the public contact form, we may collect your name, email address, telephone number, general mortgage objective, preferred contact method, selected agent and an optional short message.

Through the mortgage application, we collect the information needed to assess and prepare a mortgage request: your name, date of birth, contact details, marital status and dependants, Social Insurance Number, address and housing history, employment and income details, assets, liabilities and debts, property details, and any supporting documents you upload, together with the credit-use acknowledgement and consent records connected to your application.

Through the candidate portal, we may collect account and security information, contact details, application answers, employment and education history, optional résumés and cover letters, application status and communications, interview and review records, onboarding task information, controlled-document acknowledgements, external-signing workflow references and other onboarding-status records.

The public contact form is not a full mortgage application. Do not send a SIN, detailed banking or credit information, tax records, identity documents or mortgage documents through a general contact form or general email.

How we use personal information
We may use personal information to:

respond to service inquiries;
communicate about mortgage services requested by you;
assess, prepare and administer your mortgage application, including credit-use consent records and document review;
administer candidate accounts, applications, review and onboarding;
protect accounts, systems and records;
maintain consent, access, security and audit evidence;
meet approved legal, regulatory, records-management and dispute-handling requirements; and
send optional marketing communications only where an appropriate consent or other lawful basis has been established.
Required and optional information
Fields identified as required are needed to process the relevant inquiry, mortgage application or candidate application. Optional fields may be left blank. If required information or a required acknowledgement is not provided, we may be unable to process or submit the request.

Service providers and disclosure
We use vetted service providers for identity, hosting, database, private file storage, security, monitoring, malware scanning, communications, mortgage applications and external signing. They may process personal information only on our instructions and only as needed to provide those services.

We do not sell personal information or permit service providers to use personal information for their own independent marketing.

Mortgage applications and credit review
Your mortgage application information is used to assess and prepare your mortgage request. It is available to the licensed mortgage professional assigned to your file and to authorized Keeper Financial staff who need it to review or administer the application. If you choose to proceed with a lender, that lender and its service providers apply their own privacy practices; review their materials before submitting information to them.

Cookies and similar technologies
The signed-in portal and the mortgage application use cookies required to establish and protect your session and your access to your application. The public website does not currently use analytics, advertising or preference cookies. If non-essential technologies are introduced, this notice will be updated and any required choices provided before they are used.

Safeguards
Keeper Financial uses administrative, technical and physical safeguards appropriate to the information and the service. Information you provide through the mortgage application is encrypted, and access is limited to authorized users. No method of transmission or storage can be guaranteed to be completely secure.

Retention
Keeper Financial retains personal information according to approved record categories and schedules. Submitted mortgage applications and their supporting documents are retained for seven years. An unsubmitted mortgage application draft is retained for 30 days of inactivity. Public inquiries, consent records, candidate drafts and applications, documents, onboarding records, and security or audit records may be retained for different periods. Where a legal hold applies, information may be retained longer until the hold is lifted.

Access, correction, export, deletion and consent questions
You may contact Keeper Financial to ask about personal information or request access, correction, export or deletion. Requests are subject to identity verification and any applicable legal, regulatory, security and records-management requirements.

To withdraw optional marketing consent, use the unsubscribe method in the communication or contact support@keeperfinancial.ca. Withdrawal does not affect service communications needed to respond to an inquiry or administer an application.

Contact
Privacy contact: Privacy Officer Email: privacy@keeperfinancial.ca 

Changes to this notice
We may update this notice when our practices or requirements change. The effective date above identifies the version currently published.`;

// Process the approved content to remove the first three lines (title, effective date, blank line)
const lines = APPROVED_CONTENT.split("\n");
const articleContentLines = lines.slice(3); // Remove "Privacy Notice", the effective date, and the blank line
const articleContent = articleContentLines.join("\n");

const sectionHeaders = [
  "Information we collect",
  "How we use personal information",
  "Required and optional information",
  "Service providers and disclosure",
  "Mortgage applications and credit review",
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
  path: "/privacy-policy",
});

export default function PrivacyPage() {
  return (
    <div className="container policy-page">
      <InteriorPageHeader
        title="Privacy Notice"
        description="Effective date: Oct 16, 2026"
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
