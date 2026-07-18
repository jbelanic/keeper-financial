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
        <p className="eyebrow">
          {candidateFlow
            ? "Secure candidate documents"
            : "Secure administration"}
        </p>
        <h1>Verify multi-factor authentication</h1>
        <p>
          {candidateFlow
            ? "Private candidate document actions require a verified TOTP authenticator. Candidate ownership and document authorization are checked separately."
            : "Administration requires a verified TOTP authenticator and an active local brokerage administrator relationship."}
        </p>
      </header>
      <Card>
        <MfaEnrollment returnTo={returnTo} />
      </Card>
    </main>
  );
}
