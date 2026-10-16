import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, InteriorPageHeader } from "@/lib/public-components";
import {
  getMortgageService,
  mortgageServices,
  brokerSummary,
  fthbRebate,
} from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const dynamicParams = false;

export function generateStaticParams() {
  return mortgageServices.map(({ slug }) => ({ slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const service = getMortgageService(slug);
  if (!service) return {};
  return createPageMetadata({
    title: service.title,
    description: service.lead,
    path: `/mortgages/${service.slug}`,
  });
}

export default async function MortgageServicePage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const service = getMortgageService(slug);
  if (!service) notFound();

  return (
    <>
      <div className="container">
        <InteriorPageHeader
          title={service.title}
          description={service.lead}
          parent={{ label: "Mortgages", href: "/mortgages" }}
        />
      </div>
      <section className="section section-no-top">
        <div className="container">
          {service.sections && service.sections.length > 0 ? (
            <div className="content-stack">
              {service.sections.map((section) => (
                <article className="prose-card" key={section.heading}>
                  {section.eyebrow ? (
                    <p className="eyebrow">{section.eyebrow}</p>
                  ) : null}
                  <h2>{section.heading}</h2>
                  {section.body?.map((paragraph) => (
                    <p key={paragraph}>{paragraph}</p>
                  ))}
                  {section.points && section.points.length > 0 ? (
                    <ul className="check-list">
                      {section.points.map((point) => (
                        <li key={point}>{point}</li>
                      ))}
                    </ul>
                  ) : null}
                </article>
              ))}
            </div>
          ) : null}
          <article className="prose-card broker-summary-card">
            {brokerSummary.eyebrow ? (
              <p className="eyebrow">{brokerSummary.eyebrow}</p>
            ) : null}
            <h2>{brokerSummary.heading}</h2>
            {brokerSummary.body?.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
            <Link className="text-link" href="/broker">
              Read more about working with a broker
              <Icon name="arrow" />
            </Link>
          </article>
          {slug === "first-time-buyers" ? (
            <p className="external-link-note">
              <Link className="text-link" href={fthbRebate.url}>
                {fthbRebate.label} (Canada Revenue Agency)
              </Link>
            </p>
          ) : null}
          <div className="content-stack">
            <article className="prose-card">
              <h2>Worth thinking about</h2>
              <ul className="check-list">
                {service.considerations.map((consideration) => (
                  <li key={consideration}>{consideration}</li>
                ))}
              </ul>
            </article>
          </div>
        </div>
      </section>
      <section className="section section-muted">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="Protect sensitive information"
            title="Keep sensitive details in the secure application."
          />
          <div>
            <p>
              Email or call us for anything general. Please do not send
              financial documents, identity records, credit information or debt
              details — we collect those securely in the application.
            </p>
            <Link className="text-link" href="/how-it-works">
              See how the process works
            </Link>
          </div>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Choose your next step"
            description="Ask a question, or start your application."
            primaryHref="/apply"
            primaryLabel="Start your application"
            secondaryHref="/contact"
            secondaryLabel="Ask a general question"
          />
        </div>
      </section>
    </>
  );
}
