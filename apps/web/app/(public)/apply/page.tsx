import type { Metadata } from "next";
import { safeAgentAttribution } from "@/lib/lead-attribution";
import { createPageMetadata } from "@/lib/metadata";
import { ApplyPaths } from "./apply-paths";

export const metadata: Metadata = createPageMetadata({
  title: "Get started",
  description:
    "Choose a minimal contact-first request or continue through Keeper Financial’s validated secure mortgage-application route.",
  path: "/apply",
});

export default async function ApplyPage({
  searchParams,
}: {
  searchParams?: Promise<{ agent?: string | string[] }>;
}) {
  const agentSlug = safeAgentAttribution((await searchParams)?.agent);
  return <ApplyPaths agentSlug={agentSlug} />;
}
