import type { Metadata } from "next";
import { ErrorState } from "@keeper/ui";
import type { AdminAgentProfileList, EligibleAgent } from "@/lib/agent-api";
import { portalServerJson } from "@/lib/portal-server-api";
import { AgentProfileManager } from "./agent-profile-manager";

export const metadata: Metadata = { title: "Agent administration" };

export default async function AgentAdministrationPage() {
  const [result, eligibleAgents] = await Promise.all([
    portalServerJson<AdminAgentProfileList>(
      "/api/v1/admin/agent-profiles?limit=100&offset=0",
    ),
    portalServerJson<EligibleAgent[]>("/api/v1/admin/eligible-agents"),
  ]);
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Administration</p>
        <h1>Agent profiles</h1>
        <p>
          Create, edit, approve, publish, suspend, and archive public-safe
          profiles through the explicit lifecycle.
        </p>
      </header>
      {result && eligibleAgents ? (
        <AgentProfileManager
          initialProfiles={result.items}
          initialEligibleAgents={eligibleAgents}
        />
      ) : (
        <ErrorState title="Agent profile administration unavailable">
          Administration access, MFA, or the agent profile service could not be
          verified.
        </ErrorState>
      )}
    </>
  );
}
