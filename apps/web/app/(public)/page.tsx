import type { Metadata } from "next";
import Link from "next/link";
import { Card, StatusBadge } from "@keeper/ui";

export const metadata: Metadata = {
  title: "Ontario mortgage guidance",
  description:
    "Meet Keeper Financial and choose a conversation-first or secure external application path.",
};

export default function HomePage() {
  return (
    <>
      <section className="hero">
        <div className="container hero-grid">
          <div>
            <p className="eyebrow">Ontario mortgage brokerage foundation</p>
            <h1>Clear mortgage guidance starts with the right conversation.</h1>
            <p>
              This Phase 0 site establishes Keeper Financial’s accessible public
              experience while approved content and regulatory details are
              prepared.
            </p>
            <div className="button-row">
              <Link className="button-link" href="/apply">
                Explore both ways to get started
              </Link>
              <Link className="button-link button-secondary" href="/mortgages">
                Mortgage services
              </Link>
            </div>
          </div>
          <aside className="hero-panel">
            <StatusBadge tone="warning">Foundation release</StatusBadge>
            <h2>Privacy-aware by design</h2>
            <p>
              Speak with the team using minimal contact details, or continue to
              an approved external platform for a full mortgage application.
            </p>
          </aside>
        </div>
      </section>
      <section className="section">
        <div className="container">
          <p className="eyebrow">A deliberate boundary</p>
          <h2>Keeper Financial does not ask for underwriting data here.</h2>
          <div className="grid-3">
            <Card>
              <h3>Speak with someone</h3>
              <p>
                Share only basic contact information and a general objective.
              </p>
            </Card>
            <Card>
              <h3>Apply securely elsewhere</h3>
              <p>
                A validated link will direct applicants to the configured
                established provider.
              </p>
            </Card>
            <Card>
              <h3>Join the brokerage</h3>
              <p>
                A separate candidate portal supports controlled recruitment and
                onboarding.
              </p>
            </Card>
          </div>
        </div>
      </section>
    </>
  );
}
