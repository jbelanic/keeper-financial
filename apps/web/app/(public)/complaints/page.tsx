import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = {
  title: "Complaints",
  description: "Keeper Financial complaints process foundation.",
};
export default function Page() {
  return (
    <div className="container section">
      <FoundationPage
        title="Complaints"
        description="The owner-approved complaints process and regulatory escalation details must be supplied and reviewed before production."
      />
    </div>
  );
}
