import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "About Keeper Financial",
  description:
    "Learn how Keeper Financial approaches mortgage guidance, privacy-aware contact, and secure mortgage applications in Ontario.",
  path: "/about",
});

export default function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About Keeper Financial"
        title="Mortgage guidance built around clarity and the right boundaries."
        description="Keeper Financial gives Ontario mortgage clients a professional public resource, a direct way to speak with the team, and a secure route for a full application."
      >
        <div className="button-row">
          <Link className="button-link" href="/contact">
            Contact the team
          </Link>
        </div>
      </PageHero>
      <section className="section">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="Our approach"
            title="Start with understanding. Continue with purpose."
          />
          <div>
            <p>
              The public website is designed to help people understand common
              mortgage paths before they are asked for detailed information.
              General questions stay in general contact channels; a complete
              mortgage application belongs in the approved secure platform.
            </p>
            <p>
              This separation supports a simpler experience and keeps the custom
              Keeper Financial platform out of mortgage underwriting, credit,
              document collection, and lender-submission workflows.
            </p>
          </div>
        </div>
      </section>
      <section className="section section-muted">
        <div className="container value-grid">
          <article>
            <Icon name="conversation" />
            <h2>Plain language</h2>
            <p>Understand the next step without unnecessary jargon.</p>
          </article>
          <article>
            <Icon name="shield" />
            <h2>Privacy-aware contact</h2>
            <p>Share only basic contact details through the public website.</p>
          </article>
          <article>
            <Icon name="arrow" />
            <h2>Secure handoff</h2>
            <p>
              Continue to an approved external platform for a complete
              application.
            </p>
          </article>
        </div>
      </section>
      <section className="section">
        <div className="container split-feature">
          <div>
            <SectionHeading
              eyebrow="Published identity"
              title="Keeper Financial’s public details"
            />
            <p>{siteConfig.legalName}</p>
            <p>{siteConfig.regulatoryText}</p>
            <address>{siteConfig.address}</address>
          </div>
          <aside className="paper-panel">
            <h2>Speak with Keeper Financial</h2>
            <p>
              <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
            </p>
            <p>
              <a href={siteConfig.emailHref}>{siteConfig.email}</a>
            </p>
            <p>
              These are the current published public contacts. Do not email
              sensitive mortgage or identity documents.
            </p>
          </aside>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Let’s start with your general goal"
            description="Use a real contact route or compare both paths on Get Started."
            primaryHref="/apply"
            primaryLabel="Get started"
            secondaryHref="/mortgages"
            secondaryLabel="Explore mortgages"
          />
        </div>
      </section>
    </>
  );
}
