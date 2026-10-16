import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "About Keeper Financial",
  description:
    "Meet Keeper Financial, a licensed Ontario mortgage brokerage, and see how we help borrowers compare options and apply securely.",
  path: "/about",
});

export default function AboutPage() {
  return (
    <>
      <PageHero
        eyebrow="About Keeper Financial"
        title="A mortgage brokerage built around clear advice."
        description="We are a licensed Ontario brokerage. We help you understand your options, answer the questions that matter, and guide your application from start to finish."
      >
        <div className="button-row">
          <Link className="button-link" href="/contact">
            Contact us
          </Link>
        </div>
      </PageHero>
      <section className="section">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="Our approach"
            title="Advice first. Paperwork later."
          />
          <div>
            <p>
              We start with a conversation. Ask us anything — no documents, no
              pressure. When you are ready to apply, we move you into our secure
              application and keep your details protected end to end.
            </p>
            <p>
              That is also why we ask for detailed financial and identity
              information only once, in the right place, rather than through
              email.
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
            <h2>Your privacy</h2>
            <p>We ask for only what we need, when we need it.</p>
          </article>
          <article>
            <Icon name="arrow" />
            <h2>Security by design</h2>
            <p>
              Detailed financial and identity information stays inside your
              private application.
            </p>
          </article>
        </div>
      </section>
      <section className="section">
        <div className="container split-feature">
          <div>
            <SectionHeading
              eyebrow="Who we are"
              title="Brokerage information"
            />
            <p>{siteConfig.legalName}</p>
            <p>{siteConfig.regulatoryText}</p>
            <address>{siteConfig.address}</address>
          </div>
          <aside className="paper-panel">
            <h2>Contact us</h2>
            <p>
              <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
            </p>
            <p>
              <a href={siteConfig.emailHref}>{siteConfig.email}</a>
            </p>
            <p>Please do not email sensitive mortgage or identity documents.</p>
          </aside>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Let’s start with your goal"
            description="Call, email, or see both ways to begin."
            primaryHref="/apply"
            primaryLabel="Start your application"
            secondaryHref="/mortgages"
            secondaryLabel="Explore mortgages"
          />
        </div>
      </section>
    </>
  );
}
