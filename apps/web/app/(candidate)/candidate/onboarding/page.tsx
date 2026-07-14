import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = { title: "Candidate onboarding" };
export default function Page() {
  return (
    <FoundationPage
      area="candidate"
      title="Onboarding"
      description="Assigned tasks and activation gates will be available only after a controlled candidate selection."
    />
  );
}
