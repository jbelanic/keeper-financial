import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Card } from "@keeper/ui";
import { getSupabaseServerClient } from "@/lib/supabase-server";
import { safeMfaReturnTo } from "@/lib/mfa-return";
import { MfaEnrollment } from "./mfa-enrollment";

export const metadata: Metadata = {
  title: "Multi-factor authentication",
  robots: { index: false, follow: false },
};

export default async function MfaPage({
  searchParams,
}: {
  searchParams: Promise<{ returnTo?: string | string[] }>;
}) {
  const params = await searchParams;
  const returnTo = safeMfaReturnTo(params.returnTo);
  const candidateFlow = returnTo.startsWith("/candidate");
  const supabase = await getSupabaseServerClient();
  const { data, error } = await supabase.auth.getUser();
  if (error || !data.user) {
    redirect(`/auth/sign-in?returnTo=${encodeURIComponent(returnTo)}`);
  }
  return (
    <main id="main-content" className="container section">
      <Link href={candidateFlow ? returnTo : "/auth/sign-in?returnTo=/admin"}>
        ← Return to {candidateFlow ? "the candidate application" : "sign in"}
      </Link>
      <header className="foundation-header">
        <p className="eyebrow">Account security</p>
        <h1>Verify with your authenticator app</h1>
        <p>
          Enter the current code from your authenticator app to continue to
          protected documents or administration.
        </p>
      </header>
      <Card>
        <MfaEnrollment returnTo={returnTo} />
      </Card>
    </main>
  );
}
