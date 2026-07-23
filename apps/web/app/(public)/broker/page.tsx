import type { Metadata } from "next";
import Link from "next/link";
import { SectionHeading } from "@keeper/ui";
import { CtaBand, InteriorPageHeader } from "@/lib/public-components";
import { brokerInfoSections } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "Working with a mortgage broker",
  description:
    "How a mortgage broker can help you review options, compare lenders, and prepare a stronger application — general information, not an approval or rate guarantee.",
  path: "/broker",
});

export default function BrokerPage() {
  return (
    <>
      <div className="container">
        <InteriorPageHeader
          title="Working with a mortgage broker"
          description="How a mortgage broker can help you review options, compare lenders, and prepare a stronger application."
          parent={{ label: "Mortgages", href: "/mortgages" }}
        />
      </div>
      <section className="section section-no-top">
        <div className="container">
          <div className="content-stack">
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
            title="Review your mortgage options"
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
