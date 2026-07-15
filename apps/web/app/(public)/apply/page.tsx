import type { Metadata } from "next";
import { Card } from "@keeper/ui";
import { InteriorPageHeader, Icon } from "@/lib/public-components";
import { safeAgentAttribution } from "@/lib/lead-attribution";
import { createPageMetadata } from "@/lib/metadata";
import { getPublicSiteConfig, siteConfig } from "@/lib/site-config";
import { ApplyForm } from "./apply-form";

export const metadata: Metadata = createPageMetadata({
  title: "Get started",
  description:
    "Choose a minimal contact-first request or continue through Keeper Financial’s validated secure mortgage-application route.",
  path: "/apply",
});

type PublicSiteConfig = ReturnType<typeof getPublicSiteConfig>;

export function ApplyPaths({
  agentSlug,
  config = siteConfig,
  apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000",
}: {
  agentSlug?: string;
  config?: PublicSiteConfig;
  apiBase?: string;
}) {
  const attribution = agentSlug
    ? `?${new URLSearchParams({ agent: agentSlug }).toString()}`
    : "";
  return (
    <>
      <div className="container">
        <InteriorPageHeader
          title="Choose the path that works for you"
          description="Speak with Keeper Financial using minimal contact information, or continue to the approved external platform for a full mortgage application."
        />
        <p className="notice apply-warning">
          Do not submit financial, identity, health, credential, or underwriting
          information in the contact form. Use the secure full-application path
          for detailed mortgage information.
        </p>
      </div>
      <section className="section section-no-top">
        <div className="container apply-grid">
          <Card className="apply-card">
            <div className="card-icon">
              <Icon name="conversation" />
            </div>
            <p className="eyebrow">Option one</p>
            <h2>Speak with someone first</h2>
            <p>
              Provide only enough information for the team to contact you. Do
              not include sensitive financial, identity, health, credential, or
              underwriting information.
            </p>
            <p className="contact-shortcuts">
              Prefer to call?{" "}
              <a href={config.phoneHref}>{config.phoneDisplay}</a>
              {config.bookingUrl ? (
                <>
                  {" "}
                  or <a href={config.bookingUrl}>Book a call</a>
                </>
              ) : null}
            </p>
            <ApplyForm
              preferredAgentSlug={agentSlug}
              unavailableContact={`${config.phoneDisplay} or ${config.email}`}
            />
          </Card>
          <Card className="apply-card secure-application-card">
            <div className="card-icon">
              <Icon name="shield" />
            </div>
            <p className="eyebrow">Option two</p>
            <h2>Start a secure full application</h2>
            <p>
              Detailed financial and underwriting information belongs in the
              approved external mortgage-application platform—not on Keeper
              Financial’s public website.
            </p>
            <ul className="check-list">
              <li>The destination is fixed in controlled configuration.</li>
              <li>The API requires HTTPS and an exact allowed host.</li>
              <li>No destination is accepted from a visitor-supplied URL.</li>
              <li>No sensitive information is added to the redirect URL.</li>
            </ul>
            <a
              className="button-link"
              href={`${apiBase}/api/v1/integrations/mortgage-application${attribution}`}
            >
              Continue to the secure application
            </a>
            <p className="fine-print">
              You are leaving the Keeper Financial public website. Review the
              provider’s privacy and security information before submitting. If
              the provider is unavailable, call {config.phoneDisplay} or email{" "}
              {config.email}.
            </p>
          </Card>
        </div>
      </section>
    </>
  );
}

export default async function ApplyPage({
  searchParams,
}: {
  searchParams?: Promise<{ agent?: string | string[] }>;
} = {}) {
  const agentSlug = safeAgentAttribution((await searchParams)?.agent);
  return <ApplyPaths agentSlug={agentSlug} />;
}
