import type { Metadata } from "next";
import { ErrorState, Card, StatusBadge } from "@keeper/ui";
import {
  portalServerJson,
  type CandidateQueueResponse,
  type PlanSummary,
} from "@/lib/review-onboarding-api";
import { CandidateReviewPipeline } from "./candidate-review-pipeline";

export const metadata: Metadata = { title: "Candidate review queue" };

export default async function CandidateReviewQueuePage() {
  const [queue, plans] = await Promise.all([
    portalServerJson<CandidateQueueResponse>("/api/v1/admin/candidates"),
    portalServerJson<PlanSummary[]>(
      "/api/v1/admin/onboarding/plans?active=true&limit=100&offset=0",
    ),
  ]);
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
      {queue && plans ? (
        <CandidateReviewPipeline initialQueue={queue} initialPlans={plans} />
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
