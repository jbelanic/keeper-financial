import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = { title: "Agent administration" };
export default function Page() {
  return (
    <FoundationPage
      area="admin"
      title="Agents"
      description="Profile approval and publication lifecycle services are established. Editing and public rendering arrive in Phase 1E."
    />
  );
}
