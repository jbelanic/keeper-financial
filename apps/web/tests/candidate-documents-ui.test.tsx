import { fireEvent, render, screen, waitFor } from "@testing-library/react";

describe("candidate document UI", () => {
  it("announces file selection, upload progress, and quarantine state", async () => {
    const requester = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: "00000000-0000-4000-8000-000000000333",
        application_id: "00000000-0000-4000-8000-000000000111",
        category: "resume",
        original_filename: "resume.pdf",
        content_type: "application/pdf",
        size_bytes: 32,
        scan_status: "clean",
        quarantined: false,
        created_at: "2026-07-15T12:00:00Z",
      }),
    });
    const { CandidateDocuments } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
    );
    render(
      <CandidateDocuments
        applicationId="00000000-0000-4000-8000-000000000111"
        applicationState="draft"
        applicationStatus="application_started"
        requester={requester}
      />,
    );
    const file = new File(["%PDF-1.7 synthetic"], "resume.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(screen.getByLabelText(/choose candidate document/i), {
      target: { files: [file] },
    });
    expect(screen.getByRole("status")).toHaveTextContent(
      /selected resume.pdf/i,
    );
    fireEvent.click(screen.getByRole("button", { name: /upload document/i }));
    await waitFor(() => expect(requester).toHaveBeenCalledOnce());
    expect(screen.getByRole("status")).toHaveTextContent(
      /uploaded and available/i,
    );
    expect(screen.getByRole("listitem")).toHaveTextContent(
      /security scan: clean/i,
    );
  });

  it("honestly requires MFA step-up when restricted metadata is denied", async () => {
    const requester = vi.fn().mockResolvedValue({ ok: false, status: 403 });
    const { CandidateDocuments } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
    );
    render(
      <CandidateDocuments
        applicationId="00000000-0000-4000-8000-000000000111"
        applicationState="submitted"
        applicationStatus="application_submitted"
        requester={requester}
      />,
    );
    fireEvent.click(
      screen.getByRole("button", { name: /load private documents/i }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(/mfa step-up/i);
  });
});
