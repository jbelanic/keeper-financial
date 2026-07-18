import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { EmptyState, ErrorState } from "@keeper/ui";
import { getPublishedAgents } from "@/lib/agent-api";
import { createPageMetadata } from "@/lib/metadata";
import { PageHero } from "@/lib/public-components";

export const metadata: Metadata = createPageMetadata({
  title: "Our agents",
  description:
    "Browse brokerage-approved, published Keeper Financial agent profiles.",
  path: "/agents",
});

export default async function AgentsPage() {
  let result;
  try {
    result = await getPublishedAgents();
  } catch {
    result = null;
  }
  return (
    <>
      <PageHero
        eyebrow="Our agents"
        title="Brokerage-approved profiles, published with care."
        description="Find an approved Keeper Financial mortgage agent. Draft, pending, suspended, archived, and placeholder profiles never appear here."
      />
      <section
        className="section section-no-top"
        aria-labelledby="agent-directory-heading"
      >
        <div className="container reading-layout">
          <h2 id="agent-directory-heading">Published agent directory</h2>
          {result === null ? (
            <ErrorState title="Agent profiles are temporarily unavailable">
              Please try again later. No profile is shown when publication
              cannot be verified.
            </ErrorState>
          ) : result.items.length === 0 ? (
            <EmptyState title="No approved public profiles">
              Contact Keeper Financial directly for help. Profiles appear only
              after brokerage approval and explicit publication.
            </EmptyState>
          ) : (
            <div className="grid-2 agent-directory-grid">
              {result.items.map((agent) => (
                <article className="card agent-card" key={agent.slug}>
                  {agent.photo_url && agent.photo_alt_text ? (
                    <Image
                      className="agent-card-photo"
                      src={agent.photo_url}
                      alt={agent.photo_alt_text}
                      width={640}
                      height={480}
                      sizes="(max-width: 52rem) 100vw, 40vw"
                      unoptimized
                    />
                  ) : null}
                  <div>
                    <p className="eyebrow">Published profile</p>
                    <h3>{agent.licensed_name}</h3>
                    <p>{agent.approved_title}</p>
                    <p>Licence {agent.licence_number}</p>
                    {agent.service_areas.length ? (
                      <p>Serving {agent.service_areas.join(", ")}</p>
                    ) : null}
                    <Link
                      className="text-link"
                      href={`/agents/${agent.slug}`}
                      aria-label={`View ${agent.licensed_name}`}
                    >
                      View profile
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
