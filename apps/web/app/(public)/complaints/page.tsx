import type { Metadata } from "next";
import { InteriorPageHeader } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Complaints",
  description:
    "How to raise a complaint with Keeper Financial, what to include, and the Ontario regulatory escalation path through FSRA.",
  path: "/complaints",
});

export default function ComplaintsPage() {
  return (
    <div className="container policy-page">
      <InteriorPageHeader
        title="Complaints"
        description="Keeper Financial takes client concerns seriously. If you have a complaint about the mortgage services you received, please contact us so we can review the matter."
      />
      <article className="policy-content">
        <section>
          <h2>How to raise a complaint</h2>
          <p>
            Keeper Financial takes client concerns seriously. If you have a
            complaint about the mortgage services you received from Keeper
            Financial, one of our mortgage agents, or another representative of
            the brokerage, please contact us so we can review the matter.
          </p>
          <p>
            To help us understand and respond to your concern, please include:
          </p>
          <ul>
            <li>Your full name and contact information</li>
            <li>
              The name of the mortgage agent or broker involved, if applicable
            </li>
            <li>A clear description of your concern</li>
            <li>The mortgage service or application involved</li>
            <li>Relevant dates, documents, or communications</li>
            <li>How you would like Keeper Financial to respond</li>
          </ul>
          <p>
            Please do not send your Social Insurance Number, passwords, full
            banking credentials, complete account numbers, or unnecessary
            identity documents by email.
          </p>
        </section>
        <section>
          <h2>Contact information</h2>
          <p>You may submit a complaint using any of the following methods:</p>
          <ul>
            <li>
              Email:{" "}
              <a href={`mailto:${siteConfig.complaintsEmail}`}>
                {siteConfig.complaintsEmail}
              </a>
            </li>
            <li>
              Phone:{" "}
              <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
            </li>
            <li>Mail: {siteConfig.address}</li>
          </ul>
        </section>
        <section>
          <h2>What happens after we receive your complaint</h2>
          <p>
            After receiving your complaint, Keeper Financial will review the
            information provided and may contact you for additional details if
            needed.
          </p>
          <p>Our review may include:</p>
          <ul>
            <li>Confirming the nature of the concern</li>
            <li>
              Reviewing relevant records, communications, and application
              details
            </li>
            <li>
              Speaking with the mortgage agent, broker, or staff member involved
            </li>
            <li>
              Assessing whether the matter can be resolved directly with you
            </li>
            <li>
              Providing a response or next steps once the review is complete
            </li>
          </ul>
          <p>
            Keeper Financial will use the contact information you provide to
            communicate with you about the complaint.
          </p>
        </section>
        <section>
          <h2>If your complaint cannot be resolved directly</h2>
          <p>
            If you are not satisfied with Keeper Financial’s response, and your
            complaint relates to mortgage brokering conduct in Ontario, you may
            contact the Financial Services Regulatory Authority of Ontario,
            known as FSRA.
          </p>
          <p>
            FSRA regulates licensed mortgage brokerages, brokers, agents, and
            administrators in Ontario. FSRA may review complaints involving
            potential non-compliance with the Mortgage Brokerages, Lenders and
            Administrators Act, 2006 and its regulations.
          </p>
          <p>
            You can learn more or submit a complaint through{" "}
            <a
              href="https://www.fsrao.ca"
              target="_blank"
              rel="noopener noreferrer"
            >
              FSRA’s website
            </a>
            .
          </p>
        </section>
        <section>
          <h2>Important notes</h2>
          <p>
            Submitting a complaint does not guarantee a specific outcome,
            compensation, mortgage approval, rate change, or lender decision.
            Mortgage approvals, rates, terms, and conditions remain subject to
            lender review, borrower qualification, product availability, and
            applicable law.
          </p>
          <p>
            This page is intended to explain Keeper Financial’s complaint
            process. It does not limit any legal rights or regulatory options
            that may be available to you.
          </p>
        </section>
      </article>
    </div>
  );
}
