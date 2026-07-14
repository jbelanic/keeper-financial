import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = {
  title: "Careers",
  description:
    "Explore future mortgage-agent opportunities with Keeper Financial.",
};
export default function Page() {
  return (
    <div className="container section">
      <FoundationPage
        title="Build your career with Keeper Financial"
        description="Recruitment content and published opportunity listings will be implemented in Phase 1C using the controlled posting lifecycle."
      />
    </div>
  );
}
