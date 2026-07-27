"use client";
import { ErrorState } from "@keeper/ui";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main id="main-content" className="container section">
      <ErrorState>
        We could not load this page. Try again or return to the home page.
      </ErrorState>
      <button className="button" type="button" onClick={reset}>
        Try again
      </button>
    </main>
  );
}
