import type { ReactNode } from "react";
import { requirePortalAccess } from "@/lib/require-portal-access";
import { PortalShell } from "@/lib/shells";

const links: Array<[string, string]> = [
  ["Overview", "/admin"],
  ["Candidates", "/admin/candidates"],
  ["Onboarding", "/admin/onboarding"],
  ["Agents", "/admin/agents"],
  ["Content", "/admin/content"],
];

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
