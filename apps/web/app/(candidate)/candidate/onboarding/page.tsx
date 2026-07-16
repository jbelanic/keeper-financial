import type { Metadata } from "next";
import { Card, ErrorState, StatusBadge } from "@keeper/ui";
import {
  portalServerJson,
  type CandidateOnboardingDashboard,
} from "@/lib/review-onboarding-api";
import { CandidateOnboardingDashboardView } from "./candidate-onboarding-dashboard";

export const metadata: Metadata = { title: "My onboarding" };

export default async function CandidateOnboardingPage() {
  const dashboard = await portalServerJson<CandidateOnboardingDashboard>(
    "/api/v1/candidate/onboarding",
  );
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Candidate</p>
        <h1>Your onboarding</h1>
        <p>
          Complete assigned tasks, acknowledge required policies, and finish
          external signing steps. Activation is unlocked only when all required
          gates are satisfied.
        </p>
      </header>
      {dashboard ? (
        <CandidateOnboardingDashboardView dashboard={dashboard} />
      ) : (
        <Card>
          <StatusBadge tone="warning">Access unavailable</StatusBadge>
          <ErrorState title="Onboarding unavailable">
            Your candidate session or the onboarding service could not be
            verified.
          </ErrorState>
        </Card>
      )}
    </>
  );
}
