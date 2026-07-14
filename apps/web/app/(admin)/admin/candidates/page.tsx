import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = { title: "Candidate administration" };
export default function Page() {
  return (
    <FoundationPage
      area="admin"
      title="Candidates"
      description="The review queue and controlled status actions arrive in Phase 1D; backend transition policy and audit evidence are already established."
    />
  );
}
