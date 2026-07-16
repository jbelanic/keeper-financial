import { fireEvent, render, screen, within } from "@testing-library/react";
import type {
  CandidateApplication,
  CandidatePrivacyDisclosure,
} from "@/lib/recruitment-api";

const application = {
  id: "00000000-0000-4000-8000-000000000111",
  recruitment_posting_id: "00000000-0000-4000-8000-000000000222",
  source_posting_slug: "synthetic-opportunity",
  source_posting_title: "Synthetic opportunity",
  source_posting_version: 1,
  schema_version: "candidate-application-2026-07-15-v1",
  revision: 1,
  state: "draft",
  status: "application_started",
  email: "candidate@example.test",
  given_name: null,
  family_name: null,
  preferred_name: null,
  phone: null,
  city: null,
  region: null,
  country_code: null,
  preferred_contact_method: null,
  available_from: null,
  referral_source: null,
  referral_detail: null,
  interest_statement: null,
  relevant_experience: null,
  employment: [],
  education: [],
  privacy_acknowledged: false,
  information_accuracy_confirmed: false,
  privacy_disclosure_version: null,
  privacy_acknowledged_at: null,
  submitted_at: null,
  withdrawn_at: null,
  created_at: "2026-07-15T12:00:00Z",
  updated_at: "2026-07-15T12:00:00Z",
} satisfies CandidateApplication;

const disclosure = {
  title: "Candidate privacy disclosure",
  version: "candidate-privacy-disclosure-2026-07-15-v1",
  paragraphs: ["Exact server-owned privacy text."],
} satisfies CandidatePrivacyDisclosure;

describe("candidate application UI", () => {
  it("exposes persistent progress, field requirements, linked errors, and review before submission", async () => {
    const { CandidateApplicationForm } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/application-form"
    );
    render(
      <CandidateApplicationForm
        initialApplication={application}
        disclosure={disclosure}
      />,
    );
    expect(
      screen.getByRole("navigation", { name: /application progress/i }),
    ).toHaveTextContent(/contact information/i);
    expect(
      screen.getByLabelText(/first\/given name.*required/i),
    ).toBeRequired();
    expect(
      screen.getByLabelText(/preferred name.*optional/i),
    ).not.toBeRequired();
    fireEvent.click(
      screen.getByRole("button", { name: /review application/i }),
    );
    const summary = await screen.findByRole("alert");
    expect(summary).toHaveTextContent(/first\/given name is required/i);
    expect(summary).toHaveAttribute("tabindex", "-1");
    expect(
      screen.queryByRole("button", { name: /^submit application$/i }),
    ).toBeNull();
  });

  it("shows the exact server disclosure and restores focus when withdrawal is cancelled", async () => {
    const { CandidateApplicationForm } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/application-form"
    );
    render(
      <CandidateApplicationForm
        initialApplication={application}
        disclosure={disclosure}
      />,
    );
    expect(
      screen.getByText("Exact server-owned privacy text."),
    ).toBeInTheDocument();
    const withdraw = screen.getByRole("button", {
      name: /withdraw application/i,
    });
    fireEvent.click(withdraw);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(withdraw).toHaveFocus();
  });

  it("restores focus to the withdraw trigger after a successful withdrawal", async () => {
    const requestJson = vi.fn().mockResolvedValue({
      ...application,
      state: "withdrawn",
      status: "withdrawn",
      withdrawn_at: "2026-07-15T12:05:00Z",
    });
    const { CandidateApplicationForm } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/application-form"
    );
    render(
      <CandidateApplicationForm
        initialApplication={application}
        disclosure={disclosure}
        requestJson={requestJson}
      />,
    );
    const withdraw = screen.getByRole("button", { name: /withdraw application/i });
    fireEvent.click(withdraw);
    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByRole("button", { name: /confirm/i }));
    expect(await screen.findByText(/application withdrawn/i)).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();
    // Focus returns to the persistent status region, not the unmounted trigger.
    expect(screen.getByRole("status")).toHaveFocus();
  });

  it("saves the current draft before showing the submission review", async () => {
    const requestJson = vi.fn().mockResolvedValue({
      ...application,
      revision: 2,
      given_name: "Synthetic",
      family_name: "Candidate",
      phone: "+14165550100",
      city: "London",
      country_code: "CA",
      preferred_contact_method: "email",
      interest_statement: "A".repeat(100),
      privacy_acknowledged: true,
      information_accuracy_confirmed: true,
    });
    const { CandidateApplicationForm } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/application-form"
    );
    render(
      <CandidateApplicationForm
        initialApplication={application}
        disclosure={disclosure}
        requestJson={requestJson}
      />,
    );
    fireEvent.change(screen.getByLabelText(/first\/given name/i), {
      target: { value: "Synthetic" },
    });
    fireEvent.change(screen.getByLabelText(/last\/family name/i), {
      target: { value: "Candidate" },
    });
    fireEvent.change(screen.getByLabelText(/phone number/i), {
      target: { value: "+1 416 555 0100" },
    });
    fireEvent.change(screen.getByLabelText(/^city/i), {
      target: { value: "London" },
    });
    fireEvent.change(screen.getByLabelText(/preferred contact method/i), {
      target: { value: "email" },
    });
    fireEvent.change(screen.getByLabelText(/why are you interested/i), {
      target: { value: "A".repeat(100) },
    });
    fireEvent.click(
      screen.getByLabelText(/i have read the candidate privacy/i),
    );
    fireEvent.click(
      screen.getByLabelText(/information i am submitting is accurate/i),
    );
    fireEvent.click(
      screen.getByRole("button", { name: /review application/i }),
    );
    expect(
      await screen.findByRole("heading", { name: /review before submission/i }),
    ).toBeInTheDocument();
    expect(requestJson).toHaveBeenCalledWith(
      expect.stringContaining(`/candidate/applications/${application.id}`),
      expect.objectContaining({ method: "PATCH" }),
    );
  });
});
