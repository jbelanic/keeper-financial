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
  title: "Your mortgage, handled properly",
  description:
    "Compare options from multiple lenders, ask us anything, and apply online in a secure application with a licensed Ontario mortgage brokerage.",
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
        eyebrow="Ontario mortgage brokerage"
        title="Your mortgage, handled properly."
        description="Buying, renewing or refinancing? Compare options from multiple lenders, ask us anything, and apply online in a secure application."
        image="/images/home-conversation.png"
        imageAlt="A couple having a relaxed conversation in their living room"
        imagePriority
      >
        <div className="button-row">
          <Link className="button-link" href="/mortgages">
            See your options
          </Link>
          <Link className="button-link button-secondary" href="/apply">
            Start your application
          </Link>
        </div>
      </PageHero>

      <div className="container trust-strip" aria-label="What to expect">
        <div>
          <Icon name="conversation" />
          <span>
            <strong>Licensed Ontario brokers</strong>Talk to licensed mortgage
            professionals who work for you, not the lender
          </span>
        </div>
        <div>
          <Icon name="building" />
          <span>
            <strong>More lenders, one application</strong>We compare options
            from banks, credit unions and other lenders
          </span>
        </div>
        <div>
          <Icon name="shield" />
          <span>
            <strong>Your information stays private</strong>Detailed financial
            and identity details stay inside our secure application
          </span>
        </div>
      </div>

      <section className="section">
        <div className="container">
          <SectionHeading
            eyebrow="Common mortgage goals"
            title="Where would you like to begin?"
            description="Start with the topic that matches where you are today. It is general information — your rate and your approval depend on your full picture."
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
            title="A simple path to your mortgage"
            description="Ask us anything first — you will not need documents until you are ready. When you are, we move you into a secure application and stay with you from there."
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
        <div className="container">
          <SectionHeading
            eyebrow="Why Keeper Financial"
            title="Mortgage advice built around your options"
            description="We work for you, not the lender."
            align="center"
          />
          <div className="value-grid">
            <article>
              <Icon name="building" />
              <h3>More lenders to compare</h3>
              <p>
                When you work with one financial institution, you generally see
                only that institution’s mortgage products. We review options
                from multiple lenders, which may include banks, credit unions,
                monoline lenders, trust companies and alternative lenders where
                appropriate.
              </p>
            </article>
            <article>
              <Icon name="conversation" />
              <h3>Guidance, not guarantees</h3>
              <p>
                No mortgage broker can guarantee approval, a specific rate, or
                that every borrower will qualify. What we can do is help you
                understand your position, prepare a stronger application and
                compare the options that may fit.
              </p>
            </article>
            <article>
              <Icon name="shield" />
              <h3>Local, modern and secure</h3>
              <p>
                Keeper Financial combines local Ontario mortgage guidance with a
                modern online experience: start online, share information
                securely, and work with a licensed mortgage professional who can
                explain your options clearly.
              </p>
            </article>
          </div>
          <p className="section-link">
            <Link className="text-link" href="/broker">
              Read more about working with a broker <Icon name="arrow" />
            </Link>
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container split-feature">
          <div>
            <p className="eyebrow">Work with one person</p>
            <h2>Choose the agent you’d rather work with.</h2>
            <p>
              See who works in your area, then start with the person you pick.
            </p>
            <Link className="button-link" href="/agents">
              Find an Agent
            </Link>
          </div>
          <aside className="paper-panel">
            <Icon name="shield" />
            <h3>Never email us sensitive documents.</h3>
            <p>
              For your protection, we never ask for a SIN, banking details, tax
              records or identity documents by email or in a general form.
              Anything detailed happens inside the secure application.
            </p>
            <Link className="text-link" href="/contact">
              Contact us <Icon name="arrow" />
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
            title="Ready when you are"
            description="Ask a question, or start your application."
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
