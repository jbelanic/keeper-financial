import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, ErrorState } from "@keeper/ui";
import { createPageMetadata } from "@/lib/metadata";
import { getPublishedPostings } from "@/lib/recruitment-api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = createPageMetadata({
  title: "Join Keeper Financial",
  description:
    "Explore currently published opportunities with Keeper Financial.",
  path: "/careers",
});

export default async function CareersPage() {
  let result;
  try {
    result = await getPublishedPostings();
  } catch {
    result = null;
  }
  return (
    <>
      <header className="page-hero">
        <div className="container reading-layout">
          <p className="eyebrow">Opportunities</p>
          <h1>Join Keeper Financial</h1>
          <p className="page-lead">
            Explore currently published opportunities. Each posting describes
            its own responsibilities, requirements and application process. You
            do not need an account to browse.
          </p>
        </div>
      </header>
      <section className="section" aria-labelledby="opportunities-heading">
        <div className="container reading-layout">
          <h2 id="opportunities-heading">Current opportunities</h2>
          {result === null ? (
            <ErrorState title="Opportunities are temporarily unavailable">
              Please try again later.
            </ErrorState>
          ) : result.items.length === 0 ? (
            <EmptyState title="No opportunities are currently published">
              Check this page again later for future opportunities.
            </EmptyState>
          ) : (
            <div className="grid-2 posting-grid">
              {result.items.map((posting) => (
                <article className="card" key={posting.slug}>
                  <h3>{posting.title}</h3>
                  <p>{posting.summary}</p>
                  <Link
                    className="text-link"
                    href={`/careers/${posting.slug}`}
                    aria-label={`View ${posting.title}`}
                  >
                    View opportunity
                  </Link>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
