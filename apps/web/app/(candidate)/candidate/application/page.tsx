import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = { title: "Candidate application" };
export default function Page() {
  return (
    <FoundationPage
      area="candidate"
      title="Application"
      description="Draft, review, and controlled submission behavior is reserved for Phase 1C. This route already enforces candidate authorization."
    />
  );
}
