import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type {
  CandidateDetailResponse,
  CandidateQueueResponse,
} from "@/lib/review-onboarding-api";

const applicationId = "00000000-0000-4000-8000-000000000111";
const otherApplicationId = "00000000-0000-4000-8000-000000000222";
const candidateId = "00000000-0000-4000-8000-000000000333";

const queue = {
  items: [
    {
      candidate_id: candidateId,
      application_id: applicationId,
      attempt_number: 1,
      source_posting_slug: "selected-opportunity",
      source_posting_title: "Selected opportunity",
      status: "application_submitted",
      given_name: "Synthetic",
      family_name: "Candidate",
      email: "synthetic@example.test",
      interview_status: null,
      assigned_onboarding_plan_id: null,
      created_at: "2026-07-18T12:00:00Z",
      updated_at: "2026-07-18T12:00:00Z",
    },
    {
      candidate_id: candidateId,
      application_id: otherApplicationId,
      attempt_number: 1,
      source_posting_slug: "other-opportunity",
      source_posting_title: "Other opportunity",
      status: "under_review",
      given_name: "Synthetic",
      family_name: "Candidate",
      email: "synthetic@example.test",
      interview_status: null,
      assigned_onboarding_plan_id: null,
      created_at: "2026-07-18T12:00:00Z",
      updated_at: "2026-07-18T12:00:00Z",
    },
  ],
  total: 2,
  limit: 50,
  offset: 0,
} satisfies CandidateQueueResponse;

function detail(
  status: CandidateDetailResponse["status"],
): CandidateDetailResponse {
  return {
    candidate_id: candidateId,
    application_id: applicationId,
    attempt_number: 1,
    source_posting_slug: "selected-opportunity",
    source_posting_title: "Selected opportunity",
    status,
    given_name: "Synthetic",
    family_name: "Candidate",
    email: "synthetic@example.test",
    interview_status: null,
    interview_notes: null,
    interview_recorded_at: null,
    assigned_onboarding_plan_id: null,
    assigned_onboarding_at: null,
    created_at: "2026-07-18T12:00:00Z",
    updated_at: "2026-07-18T12:00:00Z",
  };
}

function jsonResponse(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(payload),
  } as Response;
}

describe("application-specific administrator information requests", () => {
  it("requires an exact eligible selected application and preserves it through review", async () => {
    const requester = vi.fn(async (path: string, init?: RequestInit) => {
      if (!init) return jsonResponse(detail("application_submitted"));
      const body = JSON.parse(String(init.body)) as { application_id?: string };
      if (path.endsWith("/decision")) {
        expect(body.application_id).toBe(applicationId);
        return jsonResponse(detail("under_review"));
      }
      if (path.endsWith("/information-requests")) {
        expect(body).toEqual({
          application_id: applicationId,
          message: "Please provide a synthetic clarification.",
        });
        return jsonResponse(
          {
            id: "00000000-0000-4000-8000-000000000444",
            candidate_id: candidateId,
            application_id: applicationId,
            status: "open",
            message: "Please provide a synthetic clarification.",
            created_at: "2026-07-18T12:00:00Z",
          },
          201,
        );
      }
      throw new Error(`unexpected path ${path}`);
    });
    const { CandidateReviewPipeline } = await import(
      "@/app/(admin)/admin/candidates/candidate-review-pipeline"
    );
    render(
      <CandidateReviewPipeline initialQueue={queue} requester={requester} />,
    );

    const initiallyDisabled = screen.getByRole("button", {
      name: /send request/i,
    });
    expect(initiallyDisabled).toBeDisabled();
    fireEvent.click(
      screen.getByRole("button", {
        name: /review synthetic for selected opportunity, attempt 1/i,
      }),
    );
    await screen.findByRole("heading", { name: /synthetic candidate/i });
    expect(screen.getAllByText(/opportunity:/i)[0]).toHaveTextContent(
      /selected opportunity.*attempt 1/i,
    );
    expect(
      screen.getByRole("button", { name: /send request/i }),
    ).toBeDisabled();
    expect(screen.getByText(/begin review first/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /begin review/i }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /send request/i }),
      ).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText(/message to candidate/i), {
      target: { value: "Please provide a synthetic clarification." },
    });
    fireEvent.click(screen.getByRole("button", { name: /send request/i }));
    expect(await screen.findByRole("status")).toHaveTextContent(
      /information request sent/i,
    );
    expect(JSON.stringify(requester.mock.calls)).not.toContain(
      otherApplicationId,
    );
  });

  it("presents an operation-specific conflict without interview wording", async () => {
    const requester = vi.fn(async (_path: string, init?: RequestInit) =>
      init ? jsonResponse({}, 409) : jsonResponse(detail("under_review")),
    );
    const { CandidateReviewPipeline } = await import(
      "@/app/(admin)/admin/candidates/candidate-review-pipeline"
    );
    render(
      <CandidateReviewPipeline initialQueue={queue} requester={requester} />,
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: /review synthetic for selected opportunity, attempt 1/i,
      }),
    );
    await screen.findByLabelText(/message to candidate/i);
    fireEvent.change(screen.getByLabelText(/message to candidate/i), {
      target: { value: "Please provide a synthetic clarification." },
    });
    fireEvent.click(screen.getByRole("button", { name: /send request/i }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/selected application is under review/i);
    expect(alert).not.toHaveTextContent(/interview status/i);
  });
});
