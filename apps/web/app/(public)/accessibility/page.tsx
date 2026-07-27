import type { Metadata } from "next";
import { InteriorPageHeader } from "@/lib/public-components";
import { createPageMetadata } from "@/lib/metadata";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = createPageMetadata({
  title: "Accessibility",
  description:
    "Keeper Financial’s public website accessibility approach, feedback contacts, and alternative-format requests.",
  path: "/accessibility",
});

export default function AccessibilityPage() {
  return (
    <div className="container policy-page">
      <InteriorPageHeader
        title="Accessibility"
        description="Keeper Financial is committed to providing a website experience that is practical, usable, and accessible to as many people as possible."
      />
      <article className="policy-content">
        <section>
          <h2>Website accessibility approach</h2>
          <p>
            Keeper Financial’s public website is designed with accessibility in
            mind, including:
          </p>
          <ul>
            <li>Clear page structure and semantic headings</li>
            <li>Keyboard-operable navigation and interactive elements</li>
            <li>Visible focus indicators for keyboard users</li>
            <li>Labelled form fields and descriptive buttons</li>
            <li>
              Content that reflows on smaller screens without page-level
              horizontal scrolling
            </li>
            <li>Error and status messages that do not rely on colour alone</li>
            <li>
              Sufficient colour contrast for core text and interface elements
            </li>
            <li>
              Reduced-motion support for non-essential animation where supported
              by the user’s device or browser settings
            </li>
            <li>Descriptive link text where practical</li>
            <li>Alternative text for meaningful images where appropriate</li>
          </ul>
          <p>
            Our goal is to support a public website experience that is
            consistent with recognized accessibility practices, including the
            Web Content Accessibility Guidelines.
          </p>
        </section>
        <section>
          <h2>Request help or share feedback</h2>
          <p>
            If you have difficulty accessing content on this website, or if you
            notice an accessibility barrier, please contact Keeper Financial.
          </p>
          <p>When contacting us, please include:</p>
          <ul>
            <li>The page or feature where you experienced the issue</li>
            <li>A description of the accessibility barrier</li>
            <li>
              The device, browser, or assistive technology you were using, if
              relevant
            </li>
            <li>Your preferred contact method if you would like a response</li>
          </ul>
          <p>
            Please do not send your Social Insurance Number, passwords, full
            banking credentials, complete account numbers, or unnecessary
            identity documents by email.
          </p>
        </section>
        <section>
          <h2>Contact information</h2>
          <ul>
            <li>
              Email: <a href={siteConfig.emailHref}>{siteConfig.email}</a>
            </li>
            <li>
              Phone:{" "}
              <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
            </li>
            <li>Mail: {siteConfig.address}</li>
          </ul>
        </section>
        <section>
          <h2>Alternative formats</h2>
          <p>
            If you need information from this website in a different format,
            contact us using the information above. Keeper Financial will review
            the request and make reasonable efforts to provide the information
            in a format that is accessible and practical in the circumstances.
          </p>
        </section>
        <section>
          <h2>Our accessibility commitment</h2>
          <p>
            Keeper Financial is committed to ensuring this website is accessible
            to the widest possible audience, regardless of ability or technology.
            We aim to meet recognized accessibility practices, including the Web
            Content Accessibility Guidelines (WCAG) 2.1 Level AA, for our public
            website and the mortgage-application experience.
          </p>
          <p>
            This commitment covers perceivable content, operable interfaces,
            understandable information, and robust markup across devices, browsers,
            and assistive technologies. We review accessibility as part of ongoing
            development and treat barriers as defects to be prioritized and
            remediated.
          </p>
        </section>
        <section>
          <h2>Ongoing review</h2>
          <p>
            Keeper Financial’s website implementation includes automated checks
            and behaviour-focused accessibility review during development.
            Accessibility is an ongoing process, and we expect to continue
            improving the website as content, technology, and user needs evolve.
          </p>
          <p>
            The accessibility statement on this page is approved site content. A
            separate formal specialist accessibility review remains a deferred
            production-readiness item, but accessibility is incorporated into the
            site and is not a standalone release blocker.
          </p>
        </section>
        <section>
          <h2>Important note</h2>
          <p>
            This page describes Keeper Financial’s current website accessibility
            approach. It does not replace any accessibility policy, legal
            obligation, or compliance process that may apply to Keeper Financial
            under Ontario accessibility law or other applicable requirements.
          </p>
        </section>
      </article>
    </div>
  );
}
