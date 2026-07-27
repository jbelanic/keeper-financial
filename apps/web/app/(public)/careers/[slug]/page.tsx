import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Breadcrumbs } from "@keeper/ui";
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
    <article className="section">
      <div className="container reading-layout">
        <Breadcrumbs
          items={[
            { label: "Careers", href: "/careers" },
            { label: posting.title },
          ]}
        />
        <header className="foundation-header">
          <p className="eyebrow">Current opportunity</p>
          <h1>{posting.title}</h1>
          <p>{posting.summary}</p>
        </header>
        <div className="posting-body">{posting.body}</div>
        <section className="posting-warnings" aria-label="Before you apply">
          <h2>Before you apply</h2>
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
          <Link className="text-link" href="/careers">
            Back to opportunities
          </Link>
        </div>
      </div>
    </article>
  );
}
