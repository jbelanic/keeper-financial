import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { Card } from "@keeper/ui";
import { SignInForm } from "./sign-in-form";

export const metadata: Metadata = {
  title: "Sign in",
  robots: { index: false, follow: false },
};
export default function Page() {
  return (
    <main id="main-content" className="container section">
      <Link href="/">← Return to public site</Link>
      <header className="foundation-header">
        <p className="eyebrow">Secure portal</p>
        <h1>Sign in</h1>
        <p>
          Supabase proves identity. Portal access also requires a verified,
          active application user, the correct local role, and an allowed
          lifecycle state.
        </p>
      </header>
      <Card>
        <Suspense fallback={<p role="status">Loading sign-in…</p>}>
          <SignInForm />
        </Suspense>
      </Card>
    </main>
  );
}
