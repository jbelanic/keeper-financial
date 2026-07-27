import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, PageHero, ServiceCard } from "@/lib/public-components";
import { mortgageServices } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "Information for the mortgage decision in front of you",
  description:
    "Review common mortgage topics in plain language. When you are ready, you can ask a general question or continue to the mortgage application.",
  path: "/mortgages",
});

const icons = ["home", "refresh", "calendar", "key", "building"] as const;

export default function MortgagesPage() {
  return (
    <>
      <PageHero
        eyebrow="Mortgage topics"
        title="Information for the mortgage decision in front of you."
        description="Review common mortgage topics in plain language. When you are ready, you can ask a general question or continue to the mortgage application."
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
            title="Choose a topic"
            description="This information is general. It does not advertise a rate, determine eligibility, or replace a review of your complete circumstances."
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
            title="General information here. Detailed information in the application."
          />
          <div>
            <p>
              Use this website for general information and basic contact
              details. Provide income, assets, liabilities, credit consent,
              identity information and supporting documents only through an
              authorized secure process.
            </p>
            <p>
              When you are ready for a complete review, the Get Started page
              links through a validated route to the configured mortgage
              application service.
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
