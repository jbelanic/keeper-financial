"use client";

import { createKeeperBrowserClient } from "@/lib/supabase-browser";
import { useState } from "react";
import { Button, ErrorSummary, FormField } from "@keeper/ui";
import { isSafePostingSlug } from "@/lib/candidate-provisioning";

export function CandidateRegistrationForm({ posting }: { posting: string }) {
  const [errors, setErrors] = useState<string[]>([]);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  if (!isSafePostingSlug(posting)) {
    return (
      <section role="alert" className="error-summary">
        <h2>This application link is unavailable</h2>
        <p>Return to careers and select a currently published opportunity.</p>
      </section>
    );
  }
  async function register(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setErrors([]);
    setStatus("");
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const supabase = createKeeperBrowserClient();
    const callback = new URL("/auth/callback", window.location.origin);
    callback.searchParams.set("posting", posting);
    const { error } = await supabase.auth.signUp({
      email: String(form.get("email")),
      password: String(form.get("password")),
      options: { emailRedirectTo: callback.toString() },
    });
    setBusy(false);
    if (error) {
      setErrors([
        "Registration could not be completed. Check the details and try again.",
      ]);
      return;
    }
    setStatus(
      "Check your email to verify the account and continue this application.",
    );
  }
  return (
    <form onSubmit={register} aria-busy={busy}>
      <ErrorSummary errors={errors} />
      <FormField id="registration-email" label="Email">
        <input
          id="registration-email"
          name="email"
          type="email"
          autoComplete="email"
          required
          disabled={busy}
        />
      </FormField>
      <FormField
        id="registration-password"
        label="Password"
        hint="Use a unique password that you do not use for another account."
      >
        <input
          id="registration-password"
          name="password"
          type="password"
          autoComplete="new-password"
          minLength={12}
          required
          disabled={busy}
        />
      </FormField>
      <Button type="submit" disabled={busy}>
        {busy ? "Creating account…" : "Create account"}
      </Button>
      {status ? <p role="status">{status}</p> : null}
    </form>
  );
}
