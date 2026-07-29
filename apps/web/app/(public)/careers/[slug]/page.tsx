import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Breadcrumbs } from "@keeper/ui";
import { recruitmentContent } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";
import { getPublishedPosting } from "@/lib/recruitment-api";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const posting = await getPublishedPosting(slug);
    if (posting) {
      return createPageMetadata({
        title: posting.title,
        description: posting.summary,
        path: `/careers/${posting.slug}`,
      });
    }
  } catch {
    // Fail closed with non-indexable metadata when publication cannot be proved.
  }
  return createPageMetadata({
    title: "Opportunity not published",
    description:
      "No approved Keeper Financial opportunity is published at this address.",
    path: "/careers",
    noIndex: true,
  });
}

export default async function CareerOpportunityPage({ params }: Props) {
  const { slug } = await params;
  let posting;
  try {
    posting = await getPublishedPosting(slug);
  } catch {
    notFound();
  }
  if (!posting) notFound();

  return (
    <article className="opportunity-page">
      <header className="opportunity-header">
        <div className="container opportunity-header-inner">
          <Breadcrumbs
            items={[
              { label: "Careers", href: "/careers" },
              { label: posting.title },
            ]}
          />
          <p className="eyebrow">Current opportunity</p>
          <h1>{posting.title}</h1>
          <p className="page-lead">{posting.summary}</p>
        </div>
      </header>

      <div className="container opportunity-content">
        <section
          className="posting-content"
          aria-labelledby="opportunity-details-heading"
        >
          <p className="eyebrow">Role overview</p>
          <h2 id="opportunity-details-heading">Opportunity details</h2>
          <div className="posting-body">{posting.body}</div>
        </section>

        <section
          className="application-steps"
          aria-labelledby="application-steps-heading"
        >
          <div className="section-heading">
            <p className="eyebrow">{recruitmentContent.application.eyebrow}</p>
            <h2 id="application-steps-heading">
              {recruitmentContent.application.heading}
            </h2>
            <p>{recruitmentContent.application.lead}</p>
          </div>
          <ol className="opportunity-step-grid">
            {recruitmentContent.application.steps.map((step, index) => (
              <li key={step.heading}>
                <span aria-hidden="true">{index + 1}</span>
                <h3>{step.heading}</h3>
                <p>{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section
          className="posting-warnings"
          aria-labelledby="before-apply-heading"
        >
          <h2 id="before-apply-heading">Before you apply</h2>
          <p>
            Submitting an application does not guarantee an interview,
            selection, onboarding, engagement or employment.
          </p>
          <p>
            Do not include government identification numbers, financial or
            health information, passwords, background-check information, licence
            numbers or documents that the application does not request.
          </p>
          <p>
            If you need an accessibility accommodation to apply, contact Keeper
            Financial before submitting your application.
          </p>
        </section>

        <section
          className="opportunity-actions"
          aria-labelledby="apply-heading"
        >
          <div>
            <p className="eyebrow">Your next step</p>
            <h2 id="apply-heading">Choose how to continue</h2>
            <p>
              New candidates can create an account. Returning candidates can
              sign in. Both paths remain tied to this opportunity.
            </p>
          </div>
          <div className="button-row">
            <Link
              className="button-link"
              href={`/auth/register?posting=${encodeURIComponent(posting.slug)}`}
            >
              Create an account
            </Link>
            <Link
              className="button-link button-secondary"
              href={`/auth/sign-in?posting=${encodeURIComponent(posting.slug)}`}
            >
              Sign in with an existing account
            </Link>
          </div>
          <Link className="text-link" href="/careers">
            Back to opportunities
          </Link>
        </section>
      </div>
    </article>
  );
}
