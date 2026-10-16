import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { EmptyState, ErrorState } from "@keeper/ui";
import { getPublishedAgents } from "@/lib/agent-api";
import { createPageMetadata } from "@/lib/metadata";
import { PageHero } from "@/lib/public-components";

export const metadata: Metadata = createPageMetadata({
  title: "Find an Agent",
  description:
    "Meet the licensed mortgage agents at Keeper Financial and contact the one you would like to work with.",
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
      <PageHero eyebrow="Find an Agent" title="Find a Keeper Financial agent" />
      <section
        className="section section-no-top"
        aria-labelledby="agents-heading"
      >
        <div className="container">
          <h2 className="visually-hidden" id="agents-heading">
            Keeper Financial agents
          </h2>
          {result === null ? (
            <ErrorState title="We can’t show our agent list right now">
              Please try again shortly, or call or email us and we will match
              you with an agent.
            </ErrorState>
          ) : result.items.length === 0 ? (
            <EmptyState title="Our agent profiles are coming soon">
              In the meantime, call or email us and we will connect you with the
              right agent.
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
