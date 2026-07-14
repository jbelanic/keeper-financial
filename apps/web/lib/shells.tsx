import Link from "next/link";
import type { ReactNode } from "react";

const publicLinks = [
  ["Mortgages", "/mortgages"],
  ["Our agents", "/agents"],
  ["Careers", "/careers"],
  ["Contact", "/contact"],
];

export function Brand() {
  return (
    <Link className="brand" href="/">
      <span className="brand-mark" aria-hidden="true">
        K
      </span>
      <span>Keeper Financial</span>
    </Link>
  );
}

export function PublicShell({ children }: { children: ReactNode }) {
  const legalName =
    process.env.NEXT_PUBLIC_BROKERAGE_LEGAL_NAME ?? "Keeper Financial";
  const licenceNumber =
    process.env.NEXT_PUBLIC_BROKERAGE_LICENCE_NUMBER ??
    "Pending owner confirmation";
  return (
    <>
      <header className="site-header">
        <div className="container nav-row">
          <Brand />
          <nav className="primary-nav" aria-label="Primary">
            <ul>
              {publicLinks.map(([label, href]) => (
                <li key={href}>
                  <Link href={href}>{label}</Link>
                </li>
              ))}
              <li>
                <Link className="nav-cta" href="/apply">
                  Get started
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>
      {children}
      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <Brand />
            <p>
              Clear guidance and a secure path to an established external
              mortgage-application provider.
            </p>
            <p className="regulatory-placeholder">
              Brokerage: {legalName}. Licence number: {licenceNumber}.
              Placeholder values are not a regulatory claim.
            </p>
          </div>
          <div>
            <h2>Explore</h2>
            <ul>
              {publicLinks.map(([label, href]) => (
                <li key={href}>
                  <Link href={href}>{label}</Link>
                </li>
              ))}
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
  area: "Candidate" | "Administration";
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
