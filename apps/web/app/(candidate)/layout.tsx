import type { Metadata } from "next";
import type { ReactNode } from "react";
import { requirePortalAccess } from "@/lib/require-portal-access";
import {
  portalServerJson,
  type CandidateOnboardingAvailability,
} from "@/lib/review-onboarding-api";
import { PortalShell } from "@/lib/shells";

const baseLinks: Array<[string, string]> = [
  ["Overview", "/candidate"],
  ["Applications", "/candidate/application"],
];

export const metadata: Metadata = {
  robots: { index: false, follow: false, noarchive: true },
};

export default async function CandidateLayout({
  children,
}: {
  children: ReactNode;
}) {
  await requirePortalAccess("candidate");
  const onboarding = await portalServerJson<CandidateOnboardingAvailability>(
    "/api/v1/candidate/onboarding/availability",
  );
  const links = onboarding?.available
    ? [
        ...baseLinks,
        ["Onboarding", "/candidate/onboarding"] as [string, string],
      ]
    : baseLinks;
  return (
    <PortalShell area="Candidate" links={links}>
      {children}
    </PortalShell>
  );
}
