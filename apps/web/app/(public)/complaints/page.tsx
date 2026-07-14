import type { Metadata } from "next";
import { InteriorPageHeader } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Complaints",
  description:
    "How to contact Keeper Financial with a complaint using the published phone, email, or postal address.",
  path: "/complaints",
});

export default function ComplaintsPage() {
  return (
    <div className="container policy-page">
      <InteriorPageHeader
        title="Complaints"
        description="Keeper Financial can receive a complaint through the published contact channels below. Final response timelines and external escalation wording require owner and regulatory review before production approval."
      />
      <article className="policy-content">
        <section>
          <h2>How to raise a complaint</h2>
          <p>
            Describe the concern, the service involved, relevant dates, and how
            you would like Keeper Financial to respond. Do not include a SIN,
            passwords, full banking details, or unnecessary identity documents.
          </p>
          <ul>
            <li>
              Email: <a href={siteConfig.emailHref}>{siteConfig.email}</a>
            </li>
            <li>
              Phone:{" "}
              <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
            </li>
            <li>Mail: {siteConfig.address}</li>
          </ul>
        </section>
        <section>
          <h2>What to expect</h2>
          <p>
            Keeper Financial should be able to identify the matter and contact
            you using the details supplied. This page does not promise an
            unapproved response time or identify an unverified complaints
            officer.
          </p>
        </section>
        <section>
          <h2>External escalation</h2>
          <p>
            The owner-approved regulatory escalation process and current wording
            have not yet been supplied. No regulator contact or legal remedy is
            fabricated on this engineering release.
          </p>
        </section>
      </article>
    </div>
  );
}
