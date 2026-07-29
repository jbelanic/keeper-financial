import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero, ServiceCard } from "@/lib/public-components";
import {
  mortgageServices,
  processSteps,
  recruitmentContent,
} from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "Start with your mortgage goal",
  description:
    "Explore common mortgage topics, ask a general question, or continue to the mortgage application when you are ready to provide detailed information.",
  path: "/",
});

const serviceIcons = [
  "home",
  "refresh",
  "calendar",
  "key",
  "building",
] as const;

export default function HomePage() {
  return (
    <>
      <PageHero
        eyebrow="Mortgage guidance"
        title="Start with your mortgage goal. Continue securely when you’re ready."
        description="Explore common mortgage topics, ask a general question, or continue to the mortgage application when you are ready to provide detailed information."
        image="/images/home-conversation.png"
        imageAlt="A couple having a relaxed conversation in their living room"
        imagePriority
      >
        <div className="button-row">
          <Link className="button-link" href="/mortgages">
            Explore mortgage topics
          </Link>
          <Link className="button-link button-secondary" href="/apply">
            Get started
          </Link>
        </div>
      </PageHero>

      <div className="container trust-strip" aria-label="What to expect">
        <div>
          <Icon name="conversation" />
          <span>
            <strong>Clear information</strong>General questions first
          </span>
        </div>
        <div>
          <Icon name="shield" />
          <span>
            <strong>General questions first</strong>Sensitive details stay in
            the application
          </span>
        </div>
        <div>
          <Icon name="building" />
          <span>
            <strong>Sensitive details stay in the application</strong>Keep
            detailed information in the mortgage application
          </span>
        </div>
      </div>

      <section className="section">
        <div className="container">
          <SectionHeading
            eyebrow="Common mortgage goals"
            title="Where would you like to begin?"
            description="Choose the topic closest to your current goal. These pages provide general information and do not determine eligibility, rates or approval."
            align="center"
          />
          <div className="service-grid">
            {mortgageServices.map((service, index) => (
              <ServiceCard
                key={service.slug}
                href={`/mortgages/${service.slug}`}
                title={service.shortTitle}
                description={service.summary}
                icon={serviceIcons[index]}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="section section-muted">
        <div className="container process-layout">
          <SectionHeading
            eyebrow="How it works"
            title="A clear first step"
            description="Choose your topic. Review general information without providing financial or identity documents. Ask a question. Contact Keeper Financial using basic contact details and non-sensitive context. Continue to the application. Use the configured mortgage application service when detailed information is required."
          />
          <ol className="process-list">
            {processSteps.map((step, index) => (
              <li key={step.title}>
                <span className="step-number" aria-hidden="true">
                  {index + 1}
                </span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section">
        <div className="container split-feature">
          <div>
            <p className="eyebrow">Prefer to contact a specific agent?</p>
            <h2>
              Browse currently published profiles and choose an agent to
              contact.
            </h2>
            <p>
              Browse currently published profiles and choose an agent to
              contact.
            </p>
            <Link className="button-link" href="/agents">
              Find an Agent
            </Link>
          </div>
          <aside className="paper-panel">
            <Icon name="shield" />
            <h3>Keep sensitive information out of general messages.</h3>
            <p>
              Do not send a SIN, banking information, tax records, identity
              documents, passwords or mortgage documents through a public
              contact form or general email. Use the mortgage application or
              another authorized secure channel when requested.
            </p>
            <Link className="text-link" href="/contact">
              Contact Keeper Financial <Icon name="arrow" />
            </Link>
          </aside>
        </div>
      </section>

      <section className="recruitment-feature">
        <div className="container recruitment-grid">
          <div className="recruitment-copy">
            <p className="eyebrow eyebrow-light">
              {recruitmentContent.home.eyebrow}
            </p>
            <h2>{recruitmentContent.home.heading}</h2>
            <p>{recruitmentContent.home.body}</p>
            <Link className="button-link" href="/careers">
              {recruitmentContent.home.ctaLabel}
            </Link>
          </div>
          <div className="recruitment-image">
            <Image
              src="/images/recruitment-team.png"
              alt={recruitmentContent.hero.imageAlt}
              fill
              sizes="(max-width: 832px) 100vw, 52vw"
            />
          </div>
        </div>
      </section>

      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Choose your next step"
            description="Ask a general question or continue to the mortgage application."
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
