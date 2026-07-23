import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, InteriorPageHeader } from "@/lib/public-components";
import {
  getMortgageService,
  mortgageServices,
  brokerInfoSections,
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
          <SectionHeading
            eyebrow="Why work with a broker"
            title="What a mortgage broker can do for you"
          />
          <div className="content-stack broker-info-stack">
            {brokerInfoSections.map((section) => (
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
          {slug === "first-time-buyers" ? (
            <p className="external-link-note">
              <Link className="text-link" href={fthbRebate.url}>
                {fthbRebate.label} (Canada Revenue Agency)
              </Link>
            </p>
          ) : null}
          <div className="reading-grid detail-consider">
            <article className="prose-card">
              <h2>Consider:</h2>
              <ul className="check-list">
                {service.considerations.map((consideration) => (
                  <li key={consideration}>{consideration}</li>
                ))}
              </ul>
            </article>
            <aside className="paper-panel">
              <h2>
                General information here. Detailed information in the
                application.
              </h2>
              <p>
                Use this website for general information and basic contact
                details. Provide income, assets, liabilities, credit consent,
                identity information and supporting documents only through an
                authorized secure process.
              </p>
            </aside>
          </div>
        </div>
      </section>
      <section className="section section-muted">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="Protect sensitive information"
            title="Use the right channel for each step."
          />
          <div>
            <p>
              Use the public contact routes only for a general objective and
              contact details. Do not email or submit financial documents,
              identity records, credit information, or detailed debts.
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
            description="Ask a general question or continue to the mortgage application."
            primaryHref="/apply"
            primaryLabel="Get started"
            secondaryHref="/contact"
            secondaryLabel="Ask a general question"
          />
        </div>
      </section>
    </>
  );
}
