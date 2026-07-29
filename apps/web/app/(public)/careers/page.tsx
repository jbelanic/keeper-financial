import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, ErrorState, SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero } from "@/lib/public-components";
import { recruitmentContent } from "@/lib/public-content";
import { createPageMetadata } from "@/lib/metadata";
import {
  getPublishedPostings,
  type PublicPostingSummary,
} from "@/lib/recruitment-api";

export const dynamic = "force-dynamic";

export const metadata: Metadata = createPageMetadata({
  title: "Ontario Mortgage Agent Careers | Keeper Financial",
  description:
    "Explore Ontario mortgage agent careers with Keeper Financial, including competitive compensation, autonomy, lead opportunities, coaching and brokerage support.",
  path: "/careers",
});

const benefitIcons = [
  "calendar",
  "key",
  "conversation",
  "shield",
  "building",
] as const;

function OpportunitySection({
  postings,
}: {
  postings: PublicPostingSummary[] | null;
}) {
  if (postings === null) {
    return (
      <section
        className="section section-no-top"
        aria-label="Current opportunities"
      >
        <div className="container recruitment-state">
          <ErrorState title="Opportunities are temporarily unavailable">
            Please try again later.
          </ErrorState>
        </div>
      </section>
    );
  }

  if (postings.length === 0) {
    return (
      <section
        className="section section-no-top"
        aria-label="Current opportunities"
      >
        <div className="container recruitment-state">
          <EmptyState title="No opportunities are currently published">
            Check this page again later for future opportunities.
          </EmptyState>
        </div>
      </section>
    );
  }

  if (postings.length === 1) {
    const posting = postings[0];
    return (
      <section
        className="section section-no-top"
        aria-labelledby="featured-opportunity-heading"
      >
        <div className="container">
          <article className="featured-opportunity">
            <p className="eyebrow">Featured opportunity</p>
            <h2 id="featured-opportunity-heading">{posting.title}</h2>
            <p>{posting.summary}</p>
            <Link className="button-link" href={`/careers/${posting.slug}`}>
              {recruitmentContent.hero.ctaLabel}
            </Link>
          </article>
        </div>
      </section>
    );
  }

  return (
    <section
      className="section section-no-top"
      aria-label="Current opportunities"
    >
      <div className="container">
        <SectionHeading
          eyebrow="Published roles"
          title="Current opportunities"
          description="Review each published opportunity before choosing the role you want to apply for."
        />
        <div className="posting-grid">
          {postings.map((posting) => (
            <article className="card posting-card" key={posting.slug}>
              <h3>{posting.title}</h3>
              <p>{posting.summary}</p>
              <Link
                className="text-link"
                href={`/careers/${posting.slug}`}
                aria-label={`View ${posting.title}`}
              >
                View opportunity <Icon name="arrow" />
              </Link>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export default async function CareersPage() {
  let postings: PublicPostingSummary[] | null;
  try {
    const result = await getPublishedPostings();
    postings = result.items;
  } catch {
    postings = null;
  }

  const featuredPosting = postings?.length === 1 ? postings[0] : null;

  return (
    <>
      <PageHero
        eyebrow={recruitmentContent.hero.eyebrow}
        title={recruitmentContent.hero.title}
        description={recruitmentContent.hero.lead}
        image="/images/recruitment-team.png"
        imageAlt={recruitmentContent.hero.imageAlt}
        imagePriority
        className="recruitment-hero"
      >
        {featuredPosting ? (
          <>
            <div className="button-row">
              <Link
                className="button-link"
                href={`/careers/${featuredPosting.slug}`}
              >
                {recruitmentContent.hero.ctaLabel}
              </Link>
            </div>
            <p className="hero-microcopy">{recruitmentContent.hero.ctaNote}</p>
          </>
        ) : null}
      </PageHero>

      <section
        className="section"
        aria-labelledby="recruitment-benefits-heading"
      >
        <div className="container">
          <SectionHeading
            eyebrow={recruitmentContent.benefits.eyebrow}
            title={recruitmentContent.benefits.heading}
            description={recruitmentContent.benefits.lead}
            align="center"
          />
          <div className="recruitment-benefits">
            {recruitmentContent.benefits.items.map((benefit, index) => (
              <article key={benefit.heading}>
                <Icon name={benefitIcons[index]} />
                <h3>{benefit.heading}</h3>
                <p>{benefit.body}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <OpportunitySection postings={postings} />

      <section
        className="section section-muted"
        aria-labelledby="candidate-journey-heading"
      >
        <div className="container process-layout recruitment-journey">
          <SectionHeading
            eyebrow={recruitmentContent.journey.eyebrow}
            title={recruitmentContent.journey.heading}
            description={recruitmentContent.journey.lead}
          />
          <ol className="process-list">
            {recruitmentContent.journey.steps.map((step, index) => (
              <li key={step.heading}>
                <span className="step-number" aria-hidden="true">
                  {index + 1}
                </span>
                <div>
                  <h3>{step.heading}</h3>
                  <p>{step.body}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {featuredPosting ? (
        <section className="section section-tight">
          <div className="container">
            <CtaBand
              title="Ready to review the role?"
              description="Explore the current opportunity before deciding whether to create an account and apply."
              primaryHref={`/careers/${featuredPosting.slug}`}
              primaryLabel={recruitmentContent.hero.ctaLabel}
            />
          </div>
        </section>
      ) : null}
    </>
  );
}
