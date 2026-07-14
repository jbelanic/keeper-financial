import type { ReactNode } from "react";
import { PublicShell } from "@/lib/shells";

export default function PublicLayout({ children }: { children: ReactNode }) {
  return (
    <PublicShell>
      <main id="main-content">{children}</main>
    </PublicShell>
  );
}
