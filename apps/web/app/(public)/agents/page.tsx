import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = {
  title: "Our agents",
  description:
    "Foundation route for approved Keeper Financial public agent profiles.",
};
export default function Page() {
  return (
    <div className="container section">
      <FoundationPage
        title="Our agents"
        description="Only approved and published profiles will appear here. Draft, suspended, and archived profiles remain non-public."
      />
    </div>
  );
}
