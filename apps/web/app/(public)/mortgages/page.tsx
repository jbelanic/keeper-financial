import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = {
  title: "Mortgages",
  description:
    "Foundation route for Keeper Financial mortgage service information.",
};
export default function Page() {
  return (
    <div className="container section">
      <FoundationPage
        title="Mortgages"
        description="Service content for purchases, refinances, renewals, first-time buyers, and investment properties will be approved in Phase 1A."
      />
    </div>
  );
}
