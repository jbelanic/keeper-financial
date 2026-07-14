import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = {
  title: "Privacy",
  description: "Keeper Financial privacy notice foundation.",
};
export default function Page() {
  return (
    <div className="container section">
      <FoundationPage
        title="Privacy"
        description="A legally reviewed privacy notice, retention approach, service-provider disclosure, and privacy contact must replace this foundation before production."
      />
    </div>
  );
}
