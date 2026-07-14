import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, SectionHeading } from "@keeper/ui";
import { Icon, PageHero } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";

export const metadata: Metadata = createPageMetadata({
  title: "Our agents",
  description:
    "Keeper Financial’s public agent directory displays only brokerage-approved, published profiles.",
  path: "/agents",
});

export default function AgentsPage() {
  return (
    <>
      <PageHero
        eyebrow="Our agents"
        title="Brokerage-approved profiles, published with care."
        description="Public agent pages will help visitors find an approved Keeper Financial contact. No draft, pending, suspended, archived, or sample profile is public."
      />
      <section className="section section-no-top">
        <div className="container directory-layout">
          <div>
            <SectionHeading
              eyebrow="Public directory"
              title="No agent profiles are published yet."
              description="The approval and publication workflow is scheduled for Phase 1E. This finished empty state does not stand in for a real agent record."
            />
            <EmptyState title="There are no approved public profiles">
              Contact Keeper Financial directly for help. Database-backed
              profiles will appear only after brokerage approval and explicit
              publication.
            </EmptyState>
          </div>
          <aside className="paper-panel">
            <Icon name="shield" />
            <h2>Publication is separate from editing</h2>
            <p>
              A profile is not public merely because it exists or an agent can
              edit it. Approval and an allowed publication state are required.
            </p>
            <Link className="button-link" href="/contact">
              Contact Keeper Financial
            </Link>
          </aside>
        </div>
      </section>
    </>
  );
}
