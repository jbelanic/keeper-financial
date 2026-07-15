import type { Metadata } from "next";
import Link from "next/link";
import { Card } from "@keeper/ui";
import { CandidateRegistrationForm } from "./registration-form";

export const metadata: Metadata = {
  title: "Candidate registration",
  robots: { index: false, follow: false },
};

export default async function CandidateRegistrationPage({
  searchParams,
}: {
  searchParams: Promise<{ posting?: string }>;
}) {
  const { posting = "" } = await searchParams;
  return (
    <main id="main-content" className="container section">
      <Link href="/careers">← Return to opportunities</Link>
      <header className="foundation-header">
        <p className="eyebrow">Candidate account</p>
        <h1>Create your candidate account</h1>
        <p>
          Verify your email before Keeper Financial creates narrowly scoped
          local access for the selected published posting.
        </p>
      </header>
      <Card>
        <CandidateRegistrationForm posting={posting} />
      </Card>
    </main>
  );
}
