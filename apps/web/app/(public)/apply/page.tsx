import type { Metadata } from "next";
import { Card } from "@keeper/ui";
import { InteriorPageHeader, Icon, CtaBand } from "@/lib/public-components";
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
          title="Choose how you’d like to begin"
          description="Ask a general question using basic contact details, or continue to the mortgage application when you are ready to provide detailed information."
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
            <h2>Ask a general question</h2>
            <p>
              Share your name, contact details, general mortgage objective and
              optional non-sensitive context.
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
            <h2>Continue to the mortgage application</h2>
            <p>
              Use the configured mortgage application service for detailed
              financial, credit, identity and document information.
            </p>
            <a
              className="button-link"
              href={`${apiBase}/api/v1/integrations/mortgage-application${attribution}`}
            >
              Continue to the mortgage application
            </a>
            <p className="fine-print">
              You will leave the Keeper Financial public website and enter the
              mortgage application service configured by Keeper Financial.
              Review the destination’s privacy and security information before
              providing detailed information. If the application service is
              unavailable, call {config.phoneDisplay} or email {config.email}.
            </p>
          </Card>
        </div>
      </section>
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Not ready to continue yet?"
            description="Return to the contact options if you only have a general question."
            primaryHref="/contact"
            primaryLabel="Return to contact options"
            secondaryHref="/how-it-works"
            secondaryLabel="See how the process works"
          />
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
