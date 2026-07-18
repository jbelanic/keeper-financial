import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Breadcrumbs } from "@keeper/ui";
import { getPublishedAgent } from "@/lib/agent-api";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

type Props = { params: Promise<{ slug: string }> };

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const agent = await getPublishedAgent(slug);
    if (agent) {
      return createPageMetadata({
        title: agent.licensed_name,
        description: `${agent.approved_title} at ${siteConfig.displayName}. Licence ${agent.licence_number}.`,
        path: `/agents/${agent.slug}`,
      });
    }
  } catch {
    // Fail closed with non-indexable metadata when publication cannot be proved.
  }
  return createPageMetadata({
    title: "Agent profile not published",
    description:
      "No approved Keeper Financial agent profile is published at this address.",
    path: "/agents",
    noIndex: true,
  });
}

export default async function AgentProfilePage({ params }: Props) {
  const { slug } = await params;
  let agent;
  try {
    agent = await getPublishedAgent(slug);
  } catch {
    notFound();
  }
  if (!agent) notFound();

  return (
    <article className="section agent-profile">
      <div className="container reading-layout">
        <Breadcrumbs
          items={[
            { label: "Our agents", href: "/agents" },
            { label: agent.licensed_name },
          ]}
        />
        <div className="agent-profile-header">
          {agent.photo_url && agent.photo_alt_text ? (
            <Image
              className="agent-profile-photo"
              src={agent.photo_url}
              alt={agent.photo_alt_text}
              width={720}
              height={720}
              sizes="(max-width: 52rem) 100vw, 32rem"
              unoptimized
              priority
            />
          ) : null}
          <header className="foundation-header">
            <p className="eyebrow">Published Keeper Financial agent</p>
            <h1>{agent.licensed_name}</h1>
            <p className="page-lead">{agent.approved_title}</p>
            <p>Licence {agent.licence_number}</p>
            <Link
              className="button-link"
              href={`/apply?agent=${encodeURIComponent(agent.slug)}`}
              aria-label={`Contact or apply with ${agent.licensed_name}`}
            >
              Contact or apply with this agent
            </Link>
          </header>
        </div>

        <section aria-labelledby="agent-biography-heading">
          <h2 id="agent-biography-heading">About {agent.licensed_name}</h2>
          <p className="preserve-lines">{agent.biography}</p>
        </section>

        <div className="grid-2 agent-profile-facts">
          <section className="card" aria-labelledby="agent-service-heading">
            <h2 id="agent-service-heading">Services and languages</h2>
            <dl className="profile-facts">
              <div>
                <dt>Languages</dt>
                <dd>{agent.languages.join(", ") || "Contact the brokerage"}</dd>
              </div>
              <div>
                <dt>Service areas</dt>
                <dd>{agent.service_areas.join(", ") || "Ontario"}</dd>
              </div>
              <div>
                <dt>Specialties</dt>
                <dd>{agent.specialties.join(", ") || "Mortgage guidance"}</dd>
              </div>
            </dl>
          </section>
          <section className="card" aria-labelledby="agent-contact-heading">
            <h2 id="agent-contact-heading">Approved public contact</h2>
            {agent.public_email ? (
              <p>
                <a href={`mailto:${agent.public_email}`}>
                  {agent.public_email}
                </a>
              </p>
            ) : null}
            {agent.public_phone ? (
              <p>
                <a href={`tel:${agent.public_phone.replace(/[^+\d]/g, "")}`}>
                  {agent.public_phone}
                </a>
              </p>
            ) : null}
            {agent.social_links.length ? (
              <ul className="plain-list">
                {agent.social_links.map((link) => (
                  <li key={`${link.label}-${link.url}`}>
                    <a href={link.url}>{link.label}</a>
                  </li>
                ))}
              </ul>
            ) : null}
          </section>
        </div>

        <aside
          className="paper-panel"
          aria-labelledby="brokerage-identity-heading"
        >
          <p className="eyebrow">Brokerage identity</p>
          <h2 id="brokerage-identity-heading">{siteConfig.legalName}</h2>
          <p>{siteConfig.regulatoryText}</p>
          <p>{siteConfig.address}</p>
          <p>
            <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
            {" · "}
            <a href={siteConfig.emailHref}>{siteConfig.email}</a>
          </p>
          <p className="fine-print">
            Agent-specific application attribution uses Keeper Financial’s
            controlled configuration. When no approved mapping exists, the
            external destination remains unavailable rather than falling back to
            an unverified URL.
          </p>
        </aside>
      </div>
    </article>
  );
}
