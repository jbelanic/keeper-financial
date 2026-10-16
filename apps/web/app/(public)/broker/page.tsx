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
            title="Review your mortgage options"
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
