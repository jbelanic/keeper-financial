import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, InteriorPageHeader } from "@/lib/public-components";
import { getMortgageService, mortgageServices } from "@/lib/public-content";
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
    description: service.summary,
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
          description={service.summary}
          parent={{ label: "Mortgages", href: "/mortgages" }}
        />
      </div>
      <section className="section section-no-top">
        <div className="container reading-grid">
          <article className="prose-card">
            <h2>Start with the purpose</h2>
            <p>{service.introduction}</p>
            <p>
              This information is general education. Mortgage suitability,
              rates, terms, and approval depend on a complete review by the
              appropriate parties.
            </p>
          </article>
          <aside className="paper-panel">
            <h2>Topics for an early conversation</h2>
            <ul className="check-list">
              {service.considerations.map((consideration) => (
                <li key={consideration}>{consideration}</li>
              ))}
            </ul>
          </aside>
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
            description="Talk with Keeper Financial first or continue to the approved secure application."
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
