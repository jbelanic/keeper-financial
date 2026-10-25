import type { Metadata } from "next";
import { safeAgentAttribution } from "@/lib/lead-attribution";
import { createPageMetadata } from "@/lib/metadata";
import { ApplyPaths } from "./apply-paths";

export const metadata: Metadata = createPageMetadata({
  title: "Mortgage readiness review",
  description:
    "Talk through your mortgage options before you apply — what may affect them, what to expect, and how to continue to Keeper Financial’s secure application.",
  path: "/apply",
});

export default async function ApplyPage({
  searchParams,
}: {
  searchParams?: Promise<{ agent?: string | string[] }>;
}) {
  const agentReference = safeAgentAttribution((await searchParams)?.agent);
  return <ApplyPaths agentReference={agentReference} />;
}
