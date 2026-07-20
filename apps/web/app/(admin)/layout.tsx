import type { Metadata } from "next";
import type { ReactNode } from "react";
import { requirePortalAccess } from "@/lib/require-portal-access";
import { PortalShell } from "@/lib/shells";

const links: Array<[string, string]> = [
  ["Overview", "/admin"],
  ["Leads", "/admin/leads"],
  ["Recruitment postings", "/admin/recruitment"],
  ["Candidates", "/admin/candidates"],
  ["Onboarding", "/admin/onboarding"],
  ["Agents", "/admin/agents"],
];

export const metadata: Metadata = {
  robots: { index: false, follow: false, noarchive: true },
};

export default async function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  await requirePortalAccess("admin");
  return (
    <PortalShell area="Administration" links={links}>
      {children}
    </PortalShell>
  );
}
