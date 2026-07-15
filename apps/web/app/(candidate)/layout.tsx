import type { Metadata } from "next";
import type { ReactNode } from "react";
import { requirePortalAccess } from "@/lib/require-portal-access";
import { PortalShell } from "@/lib/shells";

const links: Array<[string, string]> = [
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
  return (
    <PortalShell area="Candidate" links={links}>
      {children}
    </PortalShell>
  );
}
