import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, ErrorState, StatusBadge } from "@keeper/ui";
import { portalServerJson } from "@/lib/portal-server-api";
import type { components } from "@keeper/contracts";

type StatusList = components["schemas"]["CandidateStatusListResponse"];

const HUMAN_STATUSES: Record<string, string> = {
  draft: "Draft",
  submitted: "Submitted",
  more_information_requested: "More information requested",
  under_review: "Under review",
  interview: "Interview",
  conditionally_selected: "Conditionally selected",
  declined: "Declined",
  withdrawn: "Withdrawn",
};

function humanStatus(status: string): string {
  return HUMAN_STATUSES[status] ?? status.replaceAll("_", " ");
}

export const metadata: Metadata = { title: "Candidate portal" };

export default async function CandidateOverviewPage() {
  const result = await portalServerJson<StatusList>(
    "/api/v1/candidate/applications/status",
  );
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Candidate portal</p>
        <h1>Your application status</h1>
        <p>Review the current status and messages for each application.</p>
      </header>
      {!result ? (
        <ErrorState title="Your application status is temporarily unavailable">
          Sign in again or try later.
        </ErrorState>
      ) : result.applications.length === 0 ? (
        <EmptyState title="You have not started an application">
          Choose a currently published opportunity to begin.
        </EmptyState>
      ) : (
        <div className="grid-2">
          {result.applications.map((item) => (
            <article className="card" key={item.application_id}>
              <h2>Application status</h2>
              <p>
                <StatusBadge>{humanStatus(item.status)}</StatusBadge>
              </p>
              {item.messages.length ? (
                <ul>
                  {item.messages.map((message) => (
                    <li key={message}>{message}</li>
                  ))}
                </ul>
              ) : (
                <p>No candidate-visible messages have been added.</p>
              )}
              <Link href={`/candidate/applications/${item.application_id}`}>
                View application
              </Link>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
