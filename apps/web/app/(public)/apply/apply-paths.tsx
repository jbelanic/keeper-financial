import { CtaBand, InteriorPageHeader } from "@/lib/public-components";
import { getPublicSiteConfig, siteConfig } from "@/lib/site-config";
import { ReadinessPanel } from "./readiness-panel";

type PublicSiteConfig = ReturnType<typeof getPublicSiteConfig>;

export function ApplyPaths({
  agentReference,
  config = siteConfig,
}: {
  agentReference?: string;
  config?: PublicSiteConfig;
}) {
  return (
    <>
      <div className="container">
        {/* Owner + legal approved 2026-10-25 (decision 55(e)). Reword only on a new owner decision. */}
        <InteriorPageHeader
          eyebrow="Mortgage guidance · Ontario"
          title="Before you apply, understand your options."
          description="A mortgage decision starts with understanding your situation. Talk with Keeper Financial about your goals, the factors that may affect your options, and the next steps worth considering."
        />
        <p className="notice apply-warning">
          Please don’t send financial, identity or health details in the contact
          form — the secure application is the place for those.
        </p>
      </div>
      <ReadinessPanel agentReference={agentReference} config={config} />
      <section className="section section-tight">
        <div className="container">
          <CtaBand
            title="Prefer to talk it through first?"
            description="Call us, or use our contact page instead of the request form."
            primaryHref="/contact"
            primaryLabel="Contact us"
            secondaryHref="/how-it-works"
            secondaryLabel="See how the process works"
          />
        </div>
      </section>
    </>
  );
}
