import type { Metadata } from "next";
import { BorrowerApplicationForm } from "./borrower-application-form";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export const metadata: Metadata = {
  title: "Private mortgage application",
  description: "Start or continue a private Keeper Financial mortgage draft.",
  robots: { index: false, follow: false, nocache: true },
};

export default async function MortgageApplicationPage({
  searchParams,
}: {
  searchParams?: Promise<{ agent?: string | string[] }>;
}) {
  const rawAgent = (await searchParams)?.agent;
  const agentCode =
    typeof rawAgent === "string" && /^[a-z0-9]{8,32}$/.test(rawAgent)
      ? rawAgent
      : undefined;
  return <BorrowerApplicationForm agentCode={agentCode} />;
}
