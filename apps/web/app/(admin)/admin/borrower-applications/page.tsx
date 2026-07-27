import type { Metadata } from "next";
import { ErrorState } from "@keeper/ui";
import { getBorrowerReviewBootstrap } from "@/lib/borrower-review-api";
import { BorrowerReviewConsole } from "./review-console";

export const metadata: Metadata = { title: "Borrower application review" };

export default async function BorrowerApplicationReviewPage() {
  const [queue, eligibleAgents] = await getBorrowerReviewBootstrap();
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Administration</p>
        <h1>Borrower application review</h1>
        <p>
          Review submitted mortgage applications, assign the exact active agent,
          inspect supporting documents, and reveal SIN only through the audited
          AAL2 action.
        </p>
      </header>
      {queue && eligibleAgents ? (
        <BorrowerReviewConsole
          initialQueue={queue}
          eligibleAgents={eligibleAgents}
        />
      ) : (
        <ErrorState title="Borrower review unavailable">
          Administration access, MFA, or the borrower review service could not
          be verified.
        </ErrorState>
      )}
    </>
  );
}
