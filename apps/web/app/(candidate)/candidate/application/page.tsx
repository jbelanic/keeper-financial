import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, ErrorState, StatusBadge } from "@keeper/ui";
import { portalServerJson } from "@/lib/portal-server-api";
import type { CandidateApplicationList } from "@/lib/recruitment-api";

export const metadata: Metadata = { title: "Candidate applications" };

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

export default async function CandidateApplicationsPage() {
  const result = await portalServerJson<CandidateApplicationList>(
    "/api/v1/candidate/applications",
  );
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Candidate portal</p>
        <h1>Your applications</h1>
        <p>
          Each application is connected to a specific opportunity and
          application attempt.
        </p>
      </header>
      {!result ? (
        <ErrorState title="Applications unavailable">
          Your applications could not be loaded. Sign in again or try later.
        </ErrorState>
      ) : result.applications.length === 0 ? (
        <EmptyState title="No applications started">
          Select a currently published opportunity to start an application.
        </EmptyState>
      ) : (
        <div className="grid-2">
          {result.applications.map((application) => (
            <article className="card" key={application.id}>
              <h2>{application.source_posting_title}</h2>
              <p>
                <StatusBadge>{humanStatus(application.status)}</StatusBadge>
              </p>
              <Link href={`/candidate/applications/${application.id}`}>
                {application.state === "draft"
                  ? "Continue application"
                  : "View application"}
              </Link>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
