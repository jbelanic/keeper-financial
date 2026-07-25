import type { ReactNode } from "react";
import Link from "next/link";

export default function BorrowerApplicationLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="borrower-shell">
      <header className="borrower-header">
        <div className="container borrower-header-row">
          <span className="brand" aria-label="Keeper Financial">
            <span className="brand-mark" aria-hidden="true">
              K
            </span>
            <span className="brand-words">
              <span>Keeper</span>
              <span>Financial</span>
            </span>
          </span>
          <span className="borrower-security-label">
            <span aria-hidden="true">●</span> Private application
          </span>
        </div>
      </header>
      <main id="main-content" className="borrower-main">
        {children}
      </main>
      <footer className="borrower-footer">
        <div className="container">
          <p>
            Need general help? Return to the{" "}
            <Link href="/apply">Get started page</Link>. Do not send application
            answers by email.
          </p>
        </div>
      </footer>
    </div>
  );
}
