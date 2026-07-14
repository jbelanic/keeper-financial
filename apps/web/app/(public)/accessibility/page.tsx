import type { Metadata } from "next";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = {
  title: "Accessibility",
  description: "Keeper Financial accessibility commitment foundation.",
};
export default function Page() {
  return (
    <div className="container section">
      <FoundationPage
        title="Accessibility"
        description="This foundation uses semantic structure, visible focus, keyboard-operable navigation, responsive reflow, and labelled forms. The final statement requires owner review."
      />
    </div>
  );
}
