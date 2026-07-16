import type { Metadata } from "next";
import { ErrorState, Card, StatusBadge } from "@keeper/ui";
import {
  portalServerJson,
  type CandidateQueueResponse,
} from "@/lib/review-onboarding-api";
import { CandidateReviewPipeline } from "./candidate-review-pipeline";

export const metadata: Metadata = { title: "Candidate review queue" };

export default async function CandidateReviewQueuePage() {
  const queue = await portalServerJson<CandidateQueueResponse>(
    "/api/v1/admin/candidates",
  );
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Administration</p>
        <h1>Candidate review queue</h1>
        <p>
          Review submitted applications, record interviews, request information,
          and make controlled selection decisions. High-risk status changes
          require a reason and are recorded with actor and timestamps.
        </p>
      </header>
      {queue ? (
        <CandidateReviewPipeline initialQueue={queue} />
      ) : (
        <Card>
          <StatusBadge tone="warning">Access unavailable</StatusBadge>
          <ErrorState title="Review queue unavailable">
            Administration access, MFA, or the review service could not be
            verified.
          </ErrorState>
        </Card>
      )}
    </>
  );
}
