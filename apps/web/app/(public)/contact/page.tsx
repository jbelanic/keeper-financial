import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { Icon, PageHero } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Contact Keeper Financial",
  description:
    "Call, email, visit, or send a minimal contact request to Keeper Financial using the published contact details.",
  path: "/contact",
});

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Contact"
        title="Start with a general question."
        description="Call, email or send a basic contact request. Keep financial, identity and mortgage documents out of general messages."
      />
      <section className="section section-no-top">
        <div className="container contact-grid">
          <article className="contact-card">
            <Icon name="conversation" />
            <h2>Call</h2>
            <p>
              Speak with Keeper Financial about a general mortgage question or
              mortgage review.
            </p>
            <a className="text-link" href={siteConfig.phoneHref}>
              {siteConfig.phoneDisplay}
            </a>
          </article>
          <article className="contact-card">
            <Icon name="arrow" />
            <h2>Email</h2>
            <p>
              Use email for general questions only. Do not attach mortgage,
              financial, tax, or identity documents.
            </p>
            <a className="text-link break-anywhere" href={siteConfig.emailHref}>
              {siteConfig.email}
            </a>
          </article>
          <article className="contact-card">
            <Icon name="building" />
            <h2>Office</h2>
            <address>{siteConfig.address}</address>
          </article>
        </div>
      </section>
      <section className="section section-muted">
        <div className="container split-feature">
          <div>
            <SectionHeading
              eyebrow="Send a contact request"
              title="Share only what the team needs to respond."
              description="The Get Started form collects basic contact details, a general mortgage objective, and optional non-sensitive context."
            />
            <Link className="button-link" href="/apply">
              Go to Get Started
            </Link>
          </div>
          <aside className="paper-panel">
            <Icon name="shield" />
            <h2>Do not send sensitive information</h2>
            <p>
              Do not send a SIN, passwords, banking details, tax records, credit
              information or consent, identity documents or mortgage documents
              through general email or a public contact form.
            </p>
          </aside>
        </div>
      </section>
    </>
  );
}
