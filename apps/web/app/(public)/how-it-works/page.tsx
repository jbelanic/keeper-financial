import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero } from "@/lib/public-components";
import { processSteps } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "How the mortgage process works",
  description:
    "See how Keeper Financial separates general guidance, minimal contact, and the approved secure mortgage application.",
  path: "/how-it-works",
});

export default function HowItWorksPage() {
  return (
    <>
      <PageHero
        eyebrow="How it works"
        title="A clear path from first question to secure application."
        description="You can begin without sending detailed financial information. Understand the steps, choose a contact route, and move into the approved secure platform only when you are ready."
      >
        <div className="button-row">
          <Link className="button-link" href="/apply">
            See both start options
          </Link>
        </div>
      </PageHero>
      <section className="section">
        <div className="container numbered-cards">
          {processSteps.map((step, index) => (
            <article className="numbered-card" key={step.title}>
              <span aria-hidden="true">0{index + 1}</span>
              <h2>{step.title}</h2>
              <p>{step.description}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="section section-muted">
        <div className="container split-feature">
          <div>
            <SectionHeading
              eyebrow="Conversation first"
              title="What you can share on this website"
            />
            <ul className="check-list">
              <li>Your name and contact details</li>
              <li>A general mortgage objective</li>
              <li>Your preferred contact method</li>
              <li>A brief, non-sensitive message</li>
            </ul>
          </div>
          <aside className="paper-panel boundary-panel">
            <Icon name="shield" />
            <h2>What belongs in the secure application</h2>
            <p>
              Detailed income, assets, liabilities, credit consent, identity
              information, and supporting documents must not be sent through
              Keeper Financial’s general contact routes.
            </p>
          </aside>
        </div>
      </section>
      <section className="section">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="Keep expectations clear"
            title="Information is not an approval."
          />
          <div>
            <p>
              Public mortgage information cannot determine whether a product,
              lender, rate, or term is available or suitable. Those outcomes
              require a complete assessment and lender approval.
            </p>
            <Link className="text-link" href="/mortgages">
              Explore mortgage topics
            </Link>
          </div>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Start in the way that suits you"
            description="Ask a general question or move directly to the approved secure application."
            primaryHref="/apply"
            primaryLabel="Get started"
            secondaryHref="/contact"
            secondaryLabel="Contact Keeper Financial"
          />
        </div>
      </section>
    </>
  );
}
