"use client";

import { createBrowserClient } from "@supabase/ssr";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { Button, ErrorSummary, FormField } from "@keeper/ui";

function safeReturnTo(value: string | null): string {
  return value === "/admin" || value === "/candidate" ? value : "/candidate";
}

export function SignInForm() {
  const searchParams = useSearchParams();
  const [errors, setErrors] = useState<string[]>([]);
  async function signIn(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors([]);
    const form = new FormData(event.currentTarget);
    const supabase = createBrowserClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321",
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "local-placeholder",
    );
    const { error } = await supabase.auth.signInWithPassword({
      email: String(form.get("email")),
      password: String(form.get("password")),
    });
    if (error) {
      setErrors([
        "Sign-in failed. Check your credentials and verified account access.",
      ]);
      return;
    }
    window.location.assign(safeReturnTo(searchParams.get("returnTo")));
  }
  return (
    <form onSubmit={signIn}>
      <ErrorSummary errors={errors} />
      <FormField id="email" label="Email">
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
        />
      </FormField>
      <FormField id="password" label="Password">
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
        />
      </FormField>
      <Button type="submit">Sign in securely</Button>
    </form>
  );
}
