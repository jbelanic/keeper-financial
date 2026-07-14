import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = { title: "Content administration" };
export default function Page() {
  return (
    <FoundationPage
      area="admin"
      title="Content"
      description="A controlled content mechanism will be selected during Phase 1A; this foundation does not invent a CMS integration."
    />
  );
}
