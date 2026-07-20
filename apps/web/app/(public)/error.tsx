"use client";

import { Button, ErrorState } from "@keeper/ui";

export default function PublicError({ reset }: { reset: () => void }) {
  return (
    <section className="container section state-page">
      <ErrorState>
        We could not load this public page. Try again or return to the home
        page.
      </ErrorState>
      <Button type="button" onClick={reset}>
        Try again
      </Button>
    </section>
  );
}
