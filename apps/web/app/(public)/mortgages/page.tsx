import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, PageHero, ServiceCard } from "@/lib/public-components";
import { mortgageServices } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "Mortgage services",
  description:
    "Plain-language information about purchases, refinancing, renewals, first homes, and investment-property mortgages in Ontario.",
  path: "/mortgages",
});

const icons = ["home", "refresh", "calendar", "key", "building"] as const;

export default function MortgagesPage() {
  return (
    <>
      <PageHero
        eyebrow="Mortgage services"
        title="Information for the mortgage decision in front of you."
        description="Explore common mortgage paths in plain language, then choose whether to ask a question or continue to a secure application."
      >
        <div className="button-row">
          <Link className="button-link" href="/apply">
            Get started
          </Link>
          <Link className="button-link button-secondary" href="/how-it-works">
            How it works
          </Link>
        </div>
      </PageHero>
      <section className="section">
        <div className="container">
          <SectionHeading
            title="Choose a mortgage topic"
            description="These pages are educational. They do not advertise a rate, determine eligibility, or replace advice based on a complete application."
          />
          <div className="service-grid">
            {mortgageServices.map((service, index) => (
              <ServiceCard
                key={service.slug}
                href={`/mortgages/${service.slug}`}
                title={service.title}
                description={service.summary}
                icon={icons[index]}
              />
            ))}
          </div>
        </div>
      </section>
      <section className="section section-muted">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="A useful boundary"
            title="Education here. Detailed information in the secure platform."
          />
          <div>
            <p>
              Keeper Financial’s public pages help you frame questions and
              understand the sequence. They do not collect income, assets,
              liabilities, credit consent, identity documents, or mortgage
              documents.
            </p>
            <p>
              When you are ready for a complete review, the Get Started page
              links through a validated route to the approved external
              application platform.
            </p>
          </div>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Not sure where to begin?"
            description="Start with a general question and keep sensitive information out of your message."
            primaryHref="/contact"
            primaryLabel="Contact Keeper Financial"
            secondaryHref="/apply"
            secondaryLabel="View both start options"
          />
        </div>
      </section>
    </>
  );
}
