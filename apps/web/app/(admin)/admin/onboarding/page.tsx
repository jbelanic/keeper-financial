import type { Metadata } from "next";
import { Card, ErrorState, StatusBadge } from "@keeper/ui";
import {
  portalServerJson,
  type PlanSummary,
} from "@/lib/review-onboarding-api";
import { OnboardingAdmin } from "./onboarding-admin";

export const metadata: Metadata = { title: "Onboarding administration" };

export default async function OnboardingAdminPage() {
  const plans = await portalServerJson<PlanSummary[]>(
    "/api/v1/admin/onboarding/plans?limit=100&offset=0",
  );
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Administration</p>
        <h1>Onboarding administration</h1>
        <p>
          Manage onboarding plan templates, assign plans to selected candidates,
          link externally hosted e-signature envelopes, and satisfy activation
          gates. Activation is gated by server-owned controls only.
        </p>
      </header>
      {plans ? (
        <OnboardingAdmin initialPlans={plans} />
      ) : (
        <Card>
          <StatusBadge tone="warning">Access unavailable</StatusBadge>
          <ErrorState title="Onboarding administration unavailable">
            Administration access, MFA, or the onboarding service could not be
            verified.
          </ErrorState>
        </Card>
      )}
    </>
  );
}
