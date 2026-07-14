import type { Metadata } from "next";
import { Card } from "@keeper/ui";
import { InteriorPageHeader, Icon } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";
import { ApplyForm } from "./apply-form";

export const metadata: Metadata = createPageMetadata({
  title: "Get started",
  description:
    "Choose a minimal contact-first request or continue through Keeper Financial’s validated secure mortgage-application route.",
  path: "/apply",
});

export default function ApplyPage() {
  const apiBase =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  const applicationHost = new URL(siteConfig.mortgageApplicationUrl).hostname;

  return (
    <>
      <div className="container">
        <InteriorPageHeader
          title="Choose the path that works for you"
          description="Speak with Keeper Financial using minimal contact information, or continue to the approved external platform for a full mortgage application."
        />
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
              not submit sensitive financial or identity information.
            </p>
            <p className="contact-shortcuts">
              Prefer to call?{" "}
              <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
            </p>
            <ApplyForm
              unavailableContact={`${siteConfig.phoneDisplay} or ${siteConfig.email}`}
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
            <p className="secure-destination">
              Approved destination: <strong>{applicationHost}</strong>
            </p>
            <a
              className="button-link"
              href={`${apiBase}/api/v1/integrations/mortgage-application`}
            >
              Continue to the secure application
            </a>
            <p className="fine-print">
              You are leaving the Keeper Financial public website. Review the
              provider’s privacy and security information before submitting.
            </p>
          </Card>
        </div>
      </section>
    </>
  );
}
