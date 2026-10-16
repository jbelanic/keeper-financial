import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero } from "@/lib/public-components";
import { processSteps } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "From a general question to a complete application",
  description:
    "Ask anything general first, then move into our secure mortgage application when you are ready to share the details.",
  path: "/how-it-works",
});

export default function HowItWorksPage() {
  return (
    <>
      <PageHero
        eyebrow="How it works"
        title="From a general question to a complete application."
        description="Ask us anything general first. When you are ready to apply, we take you into a secure application — no documents needed until then."
      >
        <div className="button-row">
          <Link className="button-link" href="/apply">
            Start your application
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
              <li>A short message</li>
            </ul>
          </div>
          <aside className="paper-panel boundary-panel">
            <Icon name="shield" />
            <h2>What stays in the secure application</h2>
            <p>
              Income, assets, debts, credit consent, identity information and
              mortgage documents — never by email, and never in a general form.
            </p>
          </aside>
        </div>
      </section>
      <section className="section">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="What to expect"
            title="Real answers for your situation."
          />
          <div>
            <p>
              What is on this website is general information. Once we understand
              your goals and your details, we can tell you what is realistic for
              you — and what is not.
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
            description="Ask a question, or go straight to the application."
            primaryHref="/apply"
            primaryLabel="Start your application"
            secondaryHref="/contact"
            secondaryLabel="Contact us"
          />
        </div>
      </section>
    </>
  );
}
