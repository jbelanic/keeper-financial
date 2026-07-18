import type { Metadata } from "next";
import { ErrorState } from "@keeper/ui";
import type { AdminAgentProfileList } from "@/lib/agent-api";
import { portalServerJson } from "@/lib/portal-server-api";
import { AgentProfileManager } from "./agent-profile-manager";

export const metadata: Metadata = { title: "Agent administration" };

export default async function AgentAdministrationPage() {
  const result = await portalServerJson<AdminAgentProfileList>(
    "/api/v1/admin/agent-profiles?limit=100&offset=0",
  );
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
      {result ? (
        <AgentProfileManager initialProfiles={result.items} />
      ) : (
        <ErrorState title="Agent profile administration unavailable">
          Administration access, MFA, or the agent profile service could not be
          verified.
        </ErrorState>
      )}
    </>
  );
}
