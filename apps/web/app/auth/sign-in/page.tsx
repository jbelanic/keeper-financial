import type { Metadata } from "next";
import Link from "next/link";
import { Card } from "@keeper/ui";
import { getPublishedPosting } from "@/lib/recruitment-api";
import { SignInForm } from "./sign-in-form";

export const metadata: Metadata = {
  title: "Sign in",
  robots: { index: false, follow: false },
};
function safeReturnTo(value: string | undefined): "/candidate" | "/admin" {
  return value === "/admin" ? "/admin" : "/candidate";
}

function scalar(value: string | string[] | undefined): string | undefined {
  return typeof value === "string" ? value : undefined;
}

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{
    posting?: string | string[];
    returnTo?: string | string[];
    error?: string | string[];
  }>;
}) {
  const params = await searchParams;
  const requestedPosting = scalar(params.posting) ?? "";
  const returnTo = safeReturnTo(scalar(params.returnTo));
  let posting = null;
  if (requestedPosting) {
    try {
      posting = await getPublishedPosting(requestedPosting);
    } catch {
      // Fail closed when publication cannot be proved.
    }
  }
  const invalidPosting = Boolean(requestedPosting && !posting);
  return (
    <main id="main-content" className="container section">
      <Link href={posting ? `/careers/${posting.slug}` : "/"}>
        ← Return to {posting ? "the opportunity" : "public site"}
      </Link>
      <header className="foundation-header">
        <p className="eyebrow">Secure portal</p>
        <h1>
          {posting
            ? "Sign in to continue your application"
            : returnTo === "/admin"
              ? "Administration sign in"
              : "Sign in"}
        </h1>
        {posting ? (
          <p>
            Supabase verifies your identity. When you continue from this
            opportunity, Keeper Financial will create or reuse your candidate
            access and application. Subsequent portal access depends on your
            active account, candidate role, ownership, and application status.
          </p>
        ) : (
          <p>
            Supabase verifies your identity. Portal access also requires an
            existing active Keeper Financial account, an authorized local role,
            and an allowed lifecycle state.
          </p>
        )}
      </header>
      <Card>
        {invalidPosting ? (
          <section role="alert" className="error-summary">
            <h2>This application link is unavailable</h2>
            <p>
              Return to careers and select a currently published opportunity.
            </p>
            <p>
              <Link href="/auth/sign-in">
                Leave this flow and sign in normally
              </Link>
            </p>
          </section>
        ) : (
          <>
            {posting ? (
              <p>
                Applying for <strong>{posting.title}</strong>
              </p>
            ) : null}
            <SignInForm
              posting={posting?.slug}
              returnTo={returnTo}
              error={scalar(params.error)}
            />
            {posting ? (
              <p>
                Need an account?{" "}
                <Link
                  href={`/auth/register?posting=${encodeURIComponent(posting.slug)}`}
                >
                  Create one for this opportunity
                </Link>
                .
              </p>
            ) : returnTo === "/candidate" ? (
              <p>
                <Link href="/auth/sign-in?returnTo=/admin">
                  Brokerage administrator sign in
                </Link>
              </p>
            ) : null}
          </>
        )}
      </Card>
    </main>
  );
}
