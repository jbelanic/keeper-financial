import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero } from "@/lib/public-components";
import { processSteps } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "From a general question to a complete application",
  description:
    "Begin with general information and basic contact details. Move to the mortgage application only when you are ready to provide detailed information.",
  path: "/how-it-works",
});

export default function HowItWorksPage() {
  return (
    <>
      <PageHero
        eyebrow="How it works"
        title="From a general question to a complete application."
        description="Begin with general information and basic contact details. Move to the mortgage application only when you are ready to provide detailed information."
      >
        <div className="button-row">
          <Link className="button-link" href="/apply">
            Get started
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
            <h2>What belongs in the application</h2>
            <p>
              Provide detailed income, assets, liabilities, credit consent,
              identity information and mortgage documents only through an
              authorized secure process.
            </p>
          </aside>
        </div>
      </section>
      <section className="section">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="Keep expectations clear"
            title="Public information cannot determine your outcome."
          />
          <div>
            <p>
              Public information and an initial conversation cannot determine
              whether a particular mortgage, rate, term or approval is
              available.
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
            description="Ask a general question or move directly to the mortgage application."
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
