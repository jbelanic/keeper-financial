import type { Metadata } from "next";
import type { ReactNode } from "react";
import { requirePortalAccess } from "@/lib/require-portal-access";
import { PortalShell } from "@/lib/shells";

const links: Array<[string, string]> = [["My applications", "/agent"]];

export const metadata: Metadata = {
  robots: { index: false, follow: false, noarchive: true },
};

export default async function AgentLayout({
  children,
}: {
  children: ReactNode;
}) {
  await requirePortalAccess("agent");
  return (
    <PortalShell area="Agent" links={links}>
      {children}
    </PortalShell>
  );
}
