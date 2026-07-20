import type { Metadata } from "next";
import Link from "next/link";
import { Card } from "@keeper/ui";
import { getPublishedPosting } from "@/lib/recruitment-api";
import { CandidateRegistrationForm } from "./registration-form";

export const metadata: Metadata = {
  title: "Candidate registration",
  robots: { index: false, follow: false },
};

export default async function CandidateRegistrationPage({
  searchParams,
}: {
  searchParams: Promise<{ posting?: string | string[] }>;
}) {
  const params = await searchParams;
  const posting = typeof params.posting === "string" ? params.posting : "";
  let publishedPosting = null;
  try {
    publishedPosting = await getPublishedPosting(posting);
  } catch {
    // Fail closed when current publication cannot be proved.
  }
  return (
    <main id="main-content" className="container section">
      <Link
        href={
          publishedPosting ? `/careers/${publishedPosting.slug}` : "/careers"
        }
      >
        ← Return to {publishedPosting ? "the opportunity" : "opportunities"}
      </Link>
      <header className="foundation-header">
        <p className="eyebrow">Candidate account</p>
        <h1>Create an account to apply</h1>
        <p>
          Create an account for this opportunity. After you confirm your email
          address, you can continue to the application.
        </p>
      </header>
      <Card>
        {publishedPosting ? (
          <>
            <p>
              Applying for <strong>{publishedPosting.title}</strong>
            </p>
            <CandidateRegistrationForm posting={publishedPosting.slug} />
            <p>
              Already have an account?{" "}
              <Link
                href={`/auth/sign-in?posting=${encodeURIComponent(publishedPosting.slug)}`}
              >
                Sign in to continue this application
              </Link>
              .
            </p>
            <p>
              <Link href="/privacy">Read the candidate privacy disclosure</Link>{" "}
              before submitting your application.
            </p>
          </>
        ) : (
          <section role="alert" className="error-summary">
            <h2>This application link is unavailable</h2>
            <p>
              Return to careers and select a currently published opportunity.
            </p>
          </section>
        )}
      </Card>
    </main>
  );
}
