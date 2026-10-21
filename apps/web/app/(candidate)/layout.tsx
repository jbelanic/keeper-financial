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
  const roles = (await requirePortalAccess("candidate")) ?? [];
  const onboarding = await portalServerJson<CandidateOnboardingAvailability>(
    "/api/v1/candidate/onboarding/availability",
  );
  const links: Array<[string, string]> = [...baseLinks];
  if (onboarding?.available) {
    links.push(["Onboarding", "/candidate/onboarding"]);
  }
  // An activated agent keeps this portal for their own application history, but
  // must be able to reach the agent console (referral link, assigned work).
  if (roles.includes("agent")) {
    links.push(["Agent console", "/agent"]);
  }
  return (
    <PortalShell area="Candidate" links={links}>
      {children}
    </PortalShell>
  );
}
