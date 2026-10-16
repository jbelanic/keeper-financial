import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { Icon, PageHero } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Contact Keeper Financial",
  description:
    "Call, email, visit our London office, or send us a message — how to reach Keeper Financial in Ontario.",
  path: "/contact",
});

export default function ContactPage() {
  return (
    <>
      <PageHero
        eyebrow="Contact"
        title="Start with a general question."
        description="Call, email or send us a message and we’ll get back to you. Anything detailed belongs in the secure application."
      />
      <section className="section section-no-top">
        <div className="container contact-grid">
          <article className="contact-card">
            <Icon name="conversation" />
            <h2>Call</h2>
            <p>
              Talk to a licensed mortgage professional about what you are trying
              to do.
            </p>
            <a className="text-link" href={siteConfig.phoneHref}>
              {siteConfig.phoneDisplay}
            </a>
          </article>
          <article className="contact-card">
            <Icon name="arrow" />
            <h2>Email</h2>
            <p>
              Email us for anything general. Please do not attach documents — we
              collect those securely in the application.
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
              eyebrow="Send us a message"
              title="Tell us what you need."
            />
            <Link className="button-link" href="/apply">
              Send a message
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
