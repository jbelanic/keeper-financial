import type { Metadata } from "next";
import { InteriorPageHeader } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Accessibility",
  description:
    "Keeper Financial’s public website accessibility approach and published feedback contacts.",
  path: "/accessibility",
});

export default function AccessibilityPage() {
  return (
    <div className="container policy-page">
      <InteriorPageHeader
        title="Accessibility"
        description="Keeper Financial’s public website is designed for practical keyboard use, visible focus, semantic structure, and responsive reflow. A formal owner-approved accessibility policy remains required before production approval."
      />
      <article className="policy-content">
        <section>
          <h2>Website approach</h2>
          <ul>
            <li>A skip link and semantic page landmarks</li>
            <li>Keyboard-operable navigation and disclosures</li>
            <li>Visible focus indicators and labelled form controls</li>
            <li>
              Content that reflows at 320 CSS pixels without page-level
              horizontal scrolling
            </li>
            <li>Status and error messages that do not rely on colour alone</li>
            <li>Reduced-motion support for non-essential animation</li>
          </ul>
        </section>
        <section>
          <h2>Request help or share feedback</h2>
          <p>
            Use the published contact channels to request help accessing public
            content or to describe an accessibility barrier. No separate
            accessibility office or response timeline is asserted because one
            has not been supplied for publication.
          </p>
          <p>
            <a href={siteConfig.emailHref}>{siteConfig.email}</a> ·{" "}
            <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
          </p>
        </section>
        <section>
          <h2>Review status</h2>
          <p>
            Automated and behavior-focused checks support this implementation. A
            manual WCAG 2.1 AA audit and owner review remain production
            readiness work.
          </p>
        </section>
      </article>
    </div>
  );
}
