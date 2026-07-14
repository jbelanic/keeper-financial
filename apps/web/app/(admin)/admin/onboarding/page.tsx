import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = { title: "Onboarding administration" };
export default function Page() {
  return (
    <FoundationPage
      area="admin"
      title="Onboarding"
      description="Plan, task, controlled-document, version, and acknowledgement models are ready for Phase 1D workflow implementation."
    />
  );
}
