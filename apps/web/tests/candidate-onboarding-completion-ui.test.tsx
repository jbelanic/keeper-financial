import { render, screen } from "@testing-library/react";

describe("candidate onboarding agreement", () => {
  it("shows only the current pending signing link and completed history read-only", async () => {
    const { CandidateOnboardingDashboardView } = await import(
      "@/app/(candidate)/candidate/onboarding/candidate-onboarding-dashboard"
    );
    render(
      <CandidateOnboardingDashboardView
        dashboard={
          {
            assignment: {
              id: "00000000-0000-4000-8000-000000000001",
              candidate_id: "00000000-0000-4000-8000-000000000002",
              application_id: "00000000-0000-4000-8000-000000000003",
              onboarding_plan_id: "00000000-0000-4000-8000-000000000004",
              generation: 1,
              status: "completed",
              created_at: "2026-07-20T12:00:00Z",
            },
            tasks: [],
            gates: [],
            documents: [],
            acknowledgements: [],
            activation_ready: false,
            esign_envelopes: [
              {
                id: "00000000-0000-4000-8000-000000000010",
                candidate_id: "00000000-0000-4000-8000-000000000002",
                assignment_id: "00000000-0000-4000-8000-000000000001",
                provider: "documenso",
                status: "rejected",
                envelope_id: "old",
                envelope_url: "https://sign.keeperfinancial.ca/sign/old",
                last_synced_at: "2026-07-20T11:00:00Z",
                superseded_at: "2026-07-20T11:30:00Z",
                replacement_envelope_id: "00000000-0000-4000-8000-000000000011",
                created_at: "2026-07-20T10:00:00Z",
              },
              {
                id: "00000000-0000-4000-8000-000000000011",
                candidate_id: "00000000-0000-4000-8000-000000000002",
                assignment_id: "00000000-0000-4000-8000-000000000001",
                provider: "documenso",
                status: "sent",
                envelope_id: "current",
                envelope_url: "https://sign.keeperfinancial.ca/sign/current",
                last_synced_at: "2026-07-20T12:00:00Z",
                superseded_at: null,
                replacement_envelope_id: null,
                created_at: "2026-07-20T12:00:00Z",
              },
            ],
          } as never
        }
      />,
    );
    expect(screen.getByText(/onboarding completed/i)).toBeInTheDocument();
    expect(
      screen.queryByRole("link", {
        name: "Review and sign contractor agreement",
      }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/sign\/old/i)).not.toBeInTheDocument();
  });

  it("does not offer a rejected current envelope for signing", async () => {
    const { CandidateOnboardingDashboardView } = await import(
      "@/app/(candidate)/candidate/onboarding/candidate-onboarding-dashboard"
    );
    render(
      <CandidateOnboardingDashboardView
        dashboard={
          {
            assignment: {
              id: "00000000-0000-4000-8000-000000000001",
              candidate_id: "00000000-0000-4000-8000-000000000002",
              application_id: "00000000-0000-4000-8000-000000000003",
              onboarding_plan_id: "00000000-0000-4000-8000-000000000004",
              generation: 1,
              status: "active",
              created_at: "2026-07-20T12:00:00Z",
            },
            tasks: [],
            gates: [],
            documents: [],
            acknowledgements: [],
            activation_ready: false,
            esign_envelopes: [
              {
                id: "00000000-0000-4000-8000-000000000011",
                candidate_id: "00000000-0000-4000-8000-000000000002",
                assignment_id: "00000000-0000-4000-8000-000000000001",
                provider: "documenso",
                status: "rejected",
                envelope_id: "current",
                envelope_url: "https://sign.keeperfinancial.ca/sign/current",
                last_synced_at: "2026-07-20T12:00:00Z",
                superseded_at: null,
                replacement_envelope_id: null,
                created_at: "2026-07-20T12:00:00Z",
              },
            ],
          } as never
        }
      />,
    );
    expect(
      screen.queryByRole("link", {
        name: "Review and sign contractor agreement",
      }),
    ).not.toBeInTheDocument();
  });
});
