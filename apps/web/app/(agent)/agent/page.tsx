import type { Metadata } from "next";
import { ErrorState } from "@keeper/ui";
import { getAgentAssignedBootstrap } from "@/lib/borrower-review-api";
import { AgentAssignedConsole } from "./agent-console";

export const metadata: Metadata = { title: "My assigned applications" };

export default async function AgentApplicationsPage() {
  const queue = await getAgentAssignedBootstrap();
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Agent</p>
        <h1>My assigned applications</h1>
        <p>
          Review the borrower applications assigned to you and retrieve the full
          details needed to open the deal in your origination system.
        </p>
      </header>
      {queue ? (
        <AgentAssignedConsole initialQueue={queue} />
      ) : (
        <ErrorState title="Assigned applications unavailable">
          Agent access, MFA, or the borrower review service could not be
          verified.
        </ErrorState>
      )}
    </>
  );
}
