import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { createPageMetadata } from "@/lib/metadata";

export const dynamic = "force-static";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  await params;
  return createPageMetadata({
    title: "Agent profile not published",
    description:
      "No approved Keeper Financial agent profile is published at this address.",
    path: "/agents",
    noIndex: true,
  });
}

export default function AgentProfilePage(): never {
  notFound();
}
