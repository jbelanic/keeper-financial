import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, ErrorState, StatusBadge } from "@keeper/ui";
import { portalServerJson } from "@/lib/portal-server-api";
import type { components } from "@keeper/contracts";

type StatusList = components["schemas"]["CandidateStatusListResponse"];
export const metadata: Metadata = { title: "Candidate portal" };

export default async function CandidateOverviewPage() {
  const result = await portalServerJson<StatusList>(
    "/api/v1/candidate/applications/status",
  );
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Candidate portal</p>
        <h1>Your recruitment status</h1>
        <p>
          Status is communicated in text. Internal notes and reasons are never
          shown here.
        </p>
      </header>
      {!result ? (
        <ErrorState title="Status unavailable">
          Your candidate status could not be loaded.
        </ErrorState>
      ) : result.applications.length === 0 ? (
        <EmptyState title="No application status yet">
          Start from a published careers opportunity.
        </EmptyState>
      ) : (
        <div className="grid-2">
          {result.applications.map((item) => (
            <article className="card" key={item.application_id}>
              <h2>Application status</h2>
              <p>
                <StatusBadge>{item.status.replaceAll("_", " ")}</StatusBadge>
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
