import type { Metadata } from "next";
import { ErrorState } from "@keeper/ui";
import { portalServerJson } from "@/lib/portal-server-api";
import type {
  CandidateApplication,
  CandidatePrivacyDisclosure,
} from "@/lib/recruitment-api";
import { CandidateApplicationForm } from "./application-form";
import { CandidateDocuments } from "./candidate-documents";

export const metadata: Metadata = { title: "Candidate application" };

export default async function CandidateApplicationPage({
  params,
}: {
  params: Promise<{ applicationId: string }>;
}) {
  const { applicationId } = await params;
  const [application, disclosure] = await Promise.all([
    portalServerJson<CandidateApplication>(
      `/api/v1/candidate/applications/${encodeURIComponent(applicationId)}`,
    ),
    portalServerJson<CandidatePrivacyDisclosure>(
      "/api/v1/candidate/privacy-disclosure",
    ),
  ]);
  if (!application) {
    return (
      <ErrorState title="Application unavailable">
        This application does not exist or is not available to your candidate
        account.
      </ErrorState>
    );
  }
  if (!disclosure) {
    return (
      <ErrorState title="Applications cannot be submitted right now">
        The approved candidate privacy disclosure is unavailable. No application
        answers have been submitted.
      </ErrorState>
    );
  }
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Candidate application</p>
        <h1>{application.source_posting_title}</h1>
        <p>
          Save incomplete work, review every required section, and submit only
          when you are ready.
        </p>
      </header>
      <CandidateApplicationForm
        initialApplication={application}
        disclosure={disclosure}
      />
      <CandidateDocuments
        applicationId={application.id}
        applicationState={application.state}
        applicationStatus={application.status}
      />
    </>
  );
}
