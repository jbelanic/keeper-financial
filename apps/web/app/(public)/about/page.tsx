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
        title="Mortgage information and a clear way to take the next step."
        description="Keeper Financial helps people understand common mortgage processes, ask general questions and continue to a complete application through an authorized secure process."
      >
        <div className="button-row">
          <Link className="button-link" href="/contact">
            Contact Keeper Financial
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
              mortgage application belongs in an authorized secure process.
            </p>
            <p>
              This separation supports a simpler experience and keeps detailed
              mortgage information out of public contact routes.
            </p>
          </div>
        </div>
      </section>
      <section className="section section-muted">
        <div className="container value-grid">
          <article>
            <Icon name="conversation" />
            <h2>Plain language</h2>
            <p>We explain the next step without unnecessary jargon.</p>
          </article>
          <article>
            <Icon name="shield" />
            <h2>Information minimization</h2>
            <p>
              Public contact routes request only basic information needed to
              respond.
            </p>
          </article>
          <article>
            <Icon name="arrow" />
            <h2>Secure handoff</h2>
            <p>
              Detailed mortgage information and documents belong in the mortgage
              application or another authorized secure channel.
            </p>
          </article>
        </div>
      </section>
      <section className="section">
        <div className="container split-feature">
          <div>
            <SectionHeading
              eyebrow="Published identity"
              title="Brokerage information"
            />
            <p>{siteConfig.legalName}</p>
            <p>{siteConfig.regulatoryText}</p>
            <address>{siteConfig.address}</address>
          </div>
          <aside className="paper-panel">
            <h2>Contact Keeper Financial</h2>
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
