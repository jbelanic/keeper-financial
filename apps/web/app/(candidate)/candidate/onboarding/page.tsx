import type { Metadata } from "next";
import Link from "next/link";
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
          external signing steps. The portal calculates activation readiness;
          final activation remains a separate approved administrative step.
        </p>
      </header>
      {dashboard?.assignment ? (
        <CandidateOnboardingDashboardView dashboard={dashboard} />
      ) : dashboard ? (
        <Card>
          <StatusBadge tone="neutral">Not assigned</StatusBadge>
          <h2>Onboarding is not available yet</h2>
          <p>
            It will appear if your application advances and an onboarding plan
            is assigned. You can continue using your application portal now.
          </p>
          <Link href="/candidate/application">Return to your applications</Link>
        </Card>
      ) : (
        <Card>
          <StatusBadge tone="warning">Access unavailable</StatusBadge>
          <ErrorState title="Onboarding unavailable">
            Your candidate session or the onboarding service could not be
            verified.
          </ErrorState>
          <Link href="/candidate/onboarding">Try onboarding again</Link>
        </Card>
      )}
    </>
  );
}
