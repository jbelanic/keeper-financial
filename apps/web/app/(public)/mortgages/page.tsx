import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, PageHero, ServiceCard } from "@/lib/public-components";
import { mortgageServices } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "Mortgage help, wherever you are right now",
  description:
    "Buying your first home, renewing, refinancing or investing — start with plain-language answers, then talk to a licensed mortgage professional.",
  path: "/mortgages",
});

const icons = ["home", "refresh", "calendar", "key", "building"] as const;

export default function MortgagesPage() {
  return (
    <>
      <PageHero
        eyebrow="Mortgage topics"
        title="Mortgage help, wherever you are right now."
        description="Buying your first home, renewing, refinancing or investing? Start with plain-language answers, then talk to a licensed mortgage professional."
      >
        <div className="button-row">
          <Link className="button-link" href="/apply">
            Start your application
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
            description="This is general information: it does not quote a rate, decide eligibility, or replace a review of your situation."
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
            eyebrow="Where to start"
            title="General questions here. Detailed information in your secure application."
          />
          <div>
            <p>
              Ask us anything general, or give us your contact details. Income,
              assets, debts, credit consent, identity information and documents
              go in the secure application — never by email.
            </p>
            <p>
              When you are ready, Get started takes you straight to the secure
              mortgage application.
            </p>
          </div>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Not sure where to begin?"
            description="Ask us a question — you do not need to share anything detailed yet."
            primaryHref="/contact"
            primaryLabel="Contact us"
            secondaryHref="/apply"
            secondaryLabel="View both start options"
          />
        </div>
      </section>
    </>
  );
}
