import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, SectionHeading } from "@keeper/ui";
import { CtaBand, Icon, PageHero } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Join Keeper Financial",
  description:
    "Learn about Keeper Financial’s approach to mortgage-agent recruitment and contact the brokerage about future opportunities.",
  path: "/careers",
});

export default function CareersPage() {
  return (
    <>
      <PageHero
        eyebrow="Join Keeper Financial"
        title="Build your mortgage career with a modern Ontario brokerage."
        description="Learn how Keeper Financial is approaching a clear, controlled recruitment experience and start a confidential general conversation using the published contact routes."
        image="/images/recruitment-team.png"
        imageAlt="Three mortgage professionals talking in a modern office"
        imagePriority
      >
        <div className="button-row">
          <a className="button-link" href={siteConfig.emailHref}>
            Contact the brokerage
          </a>
          <a
            className="button-link button-secondary"
            href={siteConfig.phoneHref}
          >
            Call {siteConfig.phoneDisplay}
          </a>
        </div>
      </PageHero>
      <div
        className="container trust-strip recruitment-strip"
        aria-label="Recruitment approach"
      >
        <div>
          <Icon name="conversation" />
          <span>
            <strong>Clear communication</strong>Know the next step
          </span>
        </div>
        <div>
          <Icon name="shield" />
          <span>
            <strong>Controlled review</strong>Private candidate information
          </span>
        </div>
        <div>
          <Icon name="building" />
          <span>
            <strong>Ontario brokerage</strong>Published identity
          </span>
        </div>
        <div>
          <Icon name="arrow" />
          <span>
            <strong>Honest status</strong>No fabricated openings
          </span>
        </div>
      </div>
      <section className="section">
        <div className="container">
          <SectionHeading
            eyebrow="The intended experience"
            title="A recruitment process designed for clarity"
            description="Candidate registration, applications, documents, and posting administration are scheduled for Phase 1C and are not presented as available today."
            align="center"
          />
          <div className="value-grid four-up">
            <article>
              <Icon name="conversation" />
              <h3>Start with context</h3>
              <p>Understand the brokerage before deciding whether to apply.</p>
            </article>
            <article>
              <Icon name="shield" />
              <h3>Private by design</h3>
              <p>
                Candidate details and documents belong behind controlled access.
              </p>
            </article>
            <article>
              <Icon name="calendar" />
              <h3>Visible next steps</h3>
              <p>
                The planned workflow will show status without exposing internal
                notes.
              </p>
            </article>
            <article>
              <Icon name="building" />
              <h3>Approved representation</h3>
              <p>
                Public agent information requires brokerage approval before
                publication.
              </p>
            </article>
          </div>
        </div>
      </section>
      <section className="section section-muted">
        <div className="container reading-layout">
          <SectionHeading
            eyebrow="Current opportunities"
            title="Only approved postings will appear here."
          />
          <EmptyState title="No approved opportunities are published">
            Keeper Financial has not supplied a published recruitment posting
            for this phase. Draft, closed, archived, and placeholder postings
            are never shown as real opportunities.
          </EmptyState>
        </div>
      </section>
      <section className="section">
        <div className="container split-feature">
          <div>
            <SectionHeading
              eyebrow="Phase boundary"
              title="A polished public introduction—not a candidate workflow."
            />
            <p>
              This page provides approved public presentation only. It does not
              add candidate registration, application submission, document
              upload, onboarding, automated licensing checks, or profile
              publication.
            </p>
            <Link className="text-link" href="/privacy">
              Review the privacy boundary
            </Link>
          </div>
          <aside className="paper-panel">
            <h2>Interested in a future conversation?</h2>
            <p>
              Use the verified email or phone. Do not send identity documents,
              licence records, background material, or other candidate files
              until an approved private workflow is available.
            </p>
          </aside>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Talk with Keeper Financial"
            description="Use a published contact route for a general, confidential conversation."
            primaryHref={siteConfig.emailHref}
            primaryLabel="Email the brokerage"
            secondaryHref={siteConfig.phoneHref}
            secondaryLabel="Call the brokerage"
          />
        </div>
      </section>
    </>
  );
}
