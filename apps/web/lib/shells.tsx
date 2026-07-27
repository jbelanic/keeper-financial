import Link from "next/link";
import type { ReactNode } from "react";
import { publicNavigation } from "@/lib/public-content";
import { siteConfig } from "@/lib/site-config";

export function Brand() {
  return (
    <Link className="brand" href="/" aria-label="Keeper Financial home">
      <span className="brand-mark" aria-hidden="true">
        K
      </span>
      <span className="brand-words">
        <span>Keeper</span>
        <span>Financial</span>
      </span>
    </Link>
  );
}

export function PublicShell({ children }: { children: ReactNode }) {
  const organizationData = {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: siteConfig.displayName,
    legalName: siteConfig.legalName,
    url: siteConfig.siteUrl,
    email: siteConfig.email,
    telephone: siteConfig.phoneDisplay,
    address: {
      "@type": "PostalAddress",
      streetAddress: "380 Wellington Street, Tower B, 6th Floor",
      addressLocality: "London",
      addressRegion: "ON",
      postalCode: "N6A 5B5",
      addressCountry: "CA",
    },
  };
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationData) }}
      />
      <header className="site-header">
        <div className="container nav-row">
          <Brand />
          <nav className="primary-nav desktop-nav" aria-label="Primary">
            <ul>
              {publicNavigation.map((item) => (
                <li key={item.href}>
                  <Link href={item.href}>{item.label}</Link>
                </li>
              ))}
              <li>
                <Link className="nav-cta" href="/apply">
                  Get started
                </Link>
              </li>
            </ul>
          </nav>
          <details className="mobile-nav">
            <summary>Menu</summary>
            <nav aria-label="Mobile primary">
              <ul>
                {publicNavigation.map((item) => (
                  <li key={item.href}>
                    <Link href={item.href}>{item.label}</Link>
                  </li>
                ))}
                <li>
                  <Link className="nav-cta" href="/apply">
                    Get started
                  </Link>
                </li>
              </ul>
            </nav>
          </details>
        </div>
      </header>
      {children}
      <footer className="site-footer">
        <div className="container footer-grid">
          <div className="footer-brand">
            <Brand />
            <p>
              Plain-language mortgage information and a secure way to take the
              next step.
            </p>
            <p className="regulatory-line">
              {siteConfig.legalName} · {siteConfig.regulatoryText}
            </p>
          </div>
          <div>
            <h2>Mortgages</h2>
            <ul>
              <li>
                <Link href="/mortgages/purchase">Purchase mortgages</Link>
              </li>
              <li>
                <Link href="/mortgages/refinancing">Refinancing</Link>
              </li>
              <li>
                <Link href="/mortgages/renewals">Renewals</Link>
              </li>
              <li>
                <Link href="/mortgages/first-time-buyers">
                  First-time buyers
                </Link>
              </li>
              <li>
                <Link href="/mortgages/investment-properties">
                  Investment properties
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <h2>Company</h2>
            <ul>
              <li>
                <Link href="/about">About</Link>
              </li>
              <li>
                <Link href="/agents">Find an Agent</Link>
              </li>
              <li>
                <Link href="/careers">Join Keeper Financial</Link>
              </li>
              <li>
                <Link href="/contact">Contact</Link>
              </li>
              <li>
                <Link href="/how-it-works">How it works</Link>
              </li>
            </ul>
          </div>
          <div>
            <h2>Policies</h2>
            <ul>
              <li>
                <Link href="/privacy">Privacy</Link>
              </li>
              <li>
                <Link href="/complaints">Complaints</Link>
              </li>
              <li>
                <Link href="/accessibility">Accessibility</Link>
              </li>
            </ul>
          </div>
          <div className="footer-contact">
            <h2>Contact</h2>
            <address>
              <a href={siteConfig.phoneHref}>{siteConfig.phoneDisplay}</a>
              <br />
              <a href={siteConfig.emailHref}>{siteConfig.email}</a>
              <br />
              {siteConfig.address}
            </address>
            <Link className="button-link" href="/apply">
              Get started
            </Link>
          </div>
        </div>
        <div className="container footer-bottom">
          <p>
            © {new Date().getFullYear()} {siteConfig.legalName}. All rights
            reserved.
          </p>
          <p>
            Mortgage options are subject to borrower qualification and lender
            approval.
          </p>
        </div>
      </footer>
    </>
  );
}

export function PortalShell({
  area,
  links,
  children,
}: {
  area: "Candidate" | "Administration" | "Agent";
  links: Array<[string, string]>;
  children: ReactNode;
}) {
  return (
    <div className="portal-layout">
      <header className="portal-header">
        <div className="container nav-row">
          <Brand />
          <span className="portal-kicker">{area} portal</span>
        </div>
      </header>
      <div className="portal-body">
        <nav className="portal-nav" aria-label={`${area} portal`}>
          <ul>
            {links.map(([label, href]) => (
              <li key={href}>
                <Link href={href}>{label}</Link>
              </li>
            ))}
          </ul>
        </nav>
        <main id="main-content" className="portal-main">
          <div className="container">{children}</div>
        </main>
      </div>
    </div>
  );
}
