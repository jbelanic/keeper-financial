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
    title: "Opportunity not published",
    description:
      "No approved Keeper Financial opportunity is published at this address.",
    path: "/careers",
    noIndex: true,
  });
}

export default function CareerOpportunityPage(): never {
  notFound();
}
