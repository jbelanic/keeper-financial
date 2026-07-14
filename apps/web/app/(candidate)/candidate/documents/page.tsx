import type { Metadata } from "next";
import { FileUpload } from "@keeper/ui";
import { FoundationPage } from "@/lib/foundation-page";
export const metadata: Metadata = { title: "Candidate documents" };
export default function Page() {
  return (
    <>
      <FoundationPage
        area="candidate"
        title="Documents"
        description="Private document metadata and authorized retrieval are established. Upload orchestration and malware scanning arrive with Phase 1C/1D."
      />
      <div className="card">
        <FileUpload
          id="candidate-document"
          label="Private candidate document foundation"
          accept=".pdf,.jpg,.jpeg,.png"
        />
      </div>
    </>
  );
}
