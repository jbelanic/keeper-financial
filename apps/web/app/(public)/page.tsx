import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero, ServiceCard } from "@/lib/public-components";
import { mortgageServices, processSteps } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Ontario mortgage guidance",
  description:
    "Explore mortgage services, speak with Keeper Financial, or continue to the approved secure mortgage application.",
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
        eyebrow="Mortgage guidance for Ontario"
        title="Make your next mortgage decision with a clearer path."
        description="Start with plain-language information, a real conversation, or Keeper Financial’s approved secure application—whichever fits where you are today."
        image="/images/home-conversation.png"
        imageAlt="A couple having a relaxed conversation in their living room"
        imagePriority
      >
        <div className="button-row">
          <Link className="button-link" href="/apply">
            Get started
          </Link>
          <a
            className="button-link button-secondary"
            href={siteConfig.phoneHref}
          >
            Call {siteConfig.phoneDisplay}
          </a>
        </div>
      </PageHero>

      <div
        className="container trust-strip"
        aria-label="Keeper Financial service commitments"
      >
        <div>
          <Icon name="conversation" />
          <span>
            <strong>Conversation first</strong>Start with your questions
          </span>
        </div>
        <div>
          <Icon name="shield" />
          <span>
            <strong>Privacy-aware</strong>Keep sensitive details secure
          </span>
        </div>
        <div>
          <Icon name="building" />
          <span>
            <strong>Ontario focused</strong>Local brokerage guidance
          </span>
        </div>
        <div>
          <Icon name="arrow" />
          <span>
            <strong>Clear next steps</strong>Choose the path that fits
          </span>
        </div>
      </div>

      <section className="section">
        <div className="container">
          <SectionHeading
            eyebrow="Mortgage services"
            title="How we can help"
            description="Explore common mortgage needs without turning this website into an eligibility assessment or application."
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
            eyebrow="A straightforward process"
            title="Know what happens next"
            description="Keeper Financial separates early guidance from the secure collection of detailed mortgage information."
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
            <p className="eyebrow">Two honest ways to begin</p>
            <h2>Talk first or continue securely.</h2>
            <p>
              Use a minimal contact route if you want to discuss your goal. If
              you are ready to share detailed information, continue to the
              approved external application platform.
            </p>
            <ul className="check-list">
              <li>
                Phone and email use the published Keeper Financial contacts.
              </li>
              <li>The contact form asks only for basic information.</li>
              <li>Financial details and documents stay out of this website.</li>
            </ul>
            <Link className="button-link" href="/apply">
              Compare both paths
            </Link>
          </div>
          <aside className="paper-panel">
            <Icon name="shield" />
            <h3>Your privacy matters from the first step.</h3>
            <p>
              Never send a SIN, banking details, tax records, identification,
              passwords, or mortgage documents through a general contact form.
            </p>
            <Link className="text-link" href="/privacy">
              Read the privacy notice <Icon name="arrow" />
            </Link>
          </aside>
        </div>
      </section>

      <section className="recruitment-feature">
        <div className="container recruitment-grid">
          <div className="recruitment-copy">
            <p className="eyebrow eyebrow-light">Join Keeper Financial</p>
            <h2>Build your mortgage career with a modern Ontario brokerage.</h2>
            <p>
              Learn about the brokerage, its recruitment process, and how to
              start an honest conversation about future opportunities.
            </p>
            <Link className="button-link" href="/careers">
              Explore the brokerage
            </Link>
          </div>
          <div className="recruitment-image">
            <Image
              src="/images/recruitment-team.png"
              alt="Three mortgage professionals talking in a modern office"
              fill
              sizes="(max-width: 832px) 100vw, 52vw"
            />
          </div>
        </div>
      </section>

      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Ready for a clear next step?"
            description="Choose a conversation-first route or continue to the secure mortgage application."
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
