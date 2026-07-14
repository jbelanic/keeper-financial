import type { Metadata } from "next";
import { InteriorPageHeader } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Privacy notice",
  description:
    "How Keeper Financial’s public website handles minimal contact information and keeps mortgage application data in the secure external platform.",
  path: "/privacy",
});

export default function PrivacyPage() {
  return (
    <div className="container policy-page">
      <InteriorPageHeader
        title="Privacy notice"
        description="This notice explains the current public website boundary. Final production wording and retention periods remain subject to Keeper Financial’s legal and privacy review."
      />
      <article className="policy-content">
        <section>
          <h2>Information collected through the contact form</h2>
          <p>
            The contact-first form accepts a name, email address, telephone
            number, general mortgage objective, preferred contact method,
            optional preferred agent identifier, and an optional brief message.
            It records the required service-contact acknowledgement and records
            optional marketing consent separately only when selected.
          </p>
        </section>
        <section>
          <h2>Information not collected here</h2>
          <p>
            This website does not provide a custom full mortgage application. Do
            not submit SINs, credit information or consent, banking details, tax
            records, detailed assets or liabilities, identity documents, lender
            submissions, or mortgage documents through general contact routes.
          </p>
        </section>
        <section>
          <h2>Purpose and access</h2>
          <p>
            Minimal contact information is collected so Keeper Financial can
            respond to the requested service inquiry. Brokerage access is
            controlled by application roles and lifecycle state; authenticated
            identity alone does not grant access to private portal areas.
          </p>
        </section>
        <section>
          <h2>Secure mortgage application</h2>
          <p>
            A full mortgage application is handled through the configured
            external secure application destination. Keeper Financial’s custom
            website does not recreate or embed that origination workflow.
          </p>
        </section>
        <section>
          <h2>Retention and service providers</h2>
          <p>
            Final legal retention periods and the production service-provider
            register have not been approved and are not hard-coded on this
            website. They must be completed before production approval.
          </p>
        </section>
        <section>
          <h2>Questions</h2>
          <p>
            Use the published support route for privacy questions. No formal
            privacy-officer title is asserted here because one has not been
            supplied for publication.
          </p>
          <p>
            <a href={siteConfig.emailHref}>{siteConfig.email}</a> ·{" "}
            <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
          </p>
        </section>
      </article>
    </div>
  );
}
