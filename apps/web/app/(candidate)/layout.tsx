import type { ReactNode } from "react";
import { requirePortalAccess } from "@/lib/require-portal-access";
import { PortalShell } from "@/lib/shells";

const links: Array<[string, string]> = [
  ["Overview", "/candidate"],
  ["Application", "/candidate/application"],
  ["Onboarding", "/candidate/onboarding"],
  ["Documents", "/candidate/documents"],
];

export default async function CandidateLayout({
  children,
}: {
  children: ReactNode;
}) {
  await requirePortalAccess("candidate");
  return (
    <PortalShell area="Candidate" links={links}>
      {children}
    </PortalShell>
  );
}
