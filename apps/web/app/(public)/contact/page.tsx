import type { Metadata } from "next";
import Link from "next/link";
import { Card } from "@keeper/ui";
export const metadata: Metadata = {
  title: "Contact",
  description: "Contact Keeper Financial using approved channels.",
};
export default function Page() {
  return (
    <div className="container section">
      <header className="foundation-header">
        <p className="eyebrow">Contact</p>
        <h1>Let’s start with a conversation.</h1>
        <p>
          Approved phone, office, and booking details are pending owner
          confirmation.
        </p>
      </header>
      <Card>
        <h2>Minimal contact request</h2>
        <p>
          Use the Get Started page to provide only basic contact information and
          a general mortgage objective.
        </p>
        <Link className="button-link" href="/apply">
          Go to Get Started
        </Link>
      </Card>
    </div>
  );
}
