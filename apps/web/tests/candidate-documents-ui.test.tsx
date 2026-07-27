import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const applicationId = "00000000-0000-4000-8000-000000000111";

const document = {
  id: "00000000-0000-4000-8000-000000000333",
  application_id: applicationId,
  category: "cover_letter",
  original_filename: "letter.pdf",
  content_type: "application/pdf",
  size_bytes: 32,
  scan_status: "clean",
  quarantined: false,
  created_at: "2026-07-15T12:00:00Z",
};

function response(payload: unknown, status = 200): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(payload),
  } as Response;
}

describe("candidate document UI", () => {
  it("automatically loads an AAL2 empty state, uploads once, refreshes metadata, and preserves category", async () => {
    const requester = vi.fn(async (_path: string, init?: RequestInit) => {
      if (!init) {
        return requester.mock.calls.length === 1
          ? response({ items: [] })
          : response({ items: [document] });
      }
      return response(document, 201);
    });
    const { CandidateDocuments } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
    );
    render(
      <CandidateDocuments
        applicationId={applicationId}
        applicationState="draft"
        applicationStatus="application_started"
        requester={requester}
        inspectMfa={() => Promise.resolve("aal2")}
      />,
    );

    expect(await screen.findByText("No documents uploaded yet.")).toBeVisible();
    expect(requester).toHaveBeenCalledOnce();
    expect(
      screen.queryByRole("button", { name: /load private documents/i }),
    ).toBeNull();

    const category = screen.getByLabelText(/document category/i);
    fireEvent.change(category, { target: { value: "cover_letter" } });
    const fileInput = screen.getByLabelText(/choose candidate document/i);
    fireEvent.change(fileInput, {
      target: {
        files: [
          new File(["%PDF-1.7 synthetic"], "letter.pdf", {
            type: "application/pdf",
          }),
        ],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: /upload document/i }));

    expect(
      await screen.findByText(/uploaded, scanned, and listed successfully/i),
    ).toHaveAttribute("aria-live", "polite");
    expect(requester).toHaveBeenCalledTimes(3);
    expect(requester.mock.calls[1][1]).toMatchObject({ method: "POST" });
    expect(requester.mock.calls[2][1]).toBeUndefined();
    expect(screen.getByRole("listitem")).toHaveTextContent(
      /security scan: clean/i,
    );
    expect(category).toHaveValue("cover_letter");
    expect(fileInput).toHaveValue("");
    expect(
      screen.getByRole("button", { name: /upload document/i }),
    ).toBeDisabled();
  });

  it("prevents duplicate upload submission while the first request is pending", async () => {
    let resolveUpload!: (value: Response) => void;
    const requester = vi.fn((_path: string, init?: RequestInit) => {
      if (!init) return Promise.resolve(response({ items: [] }));
      return new Promise<Response>((resolve) => {
        resolveUpload = resolve;
      });
    });
    const { CandidateDocuments } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
    );
    render(
      <CandidateDocuments
        applicationId={applicationId}
        applicationState="draft"
        applicationStatus="application_started"
        requester={requester}
        inspectMfa={() => Promise.resolve("aal2")}
      />,
    );
    await screen.findByText("No documents uploaded yet.");
    fireEvent.change(screen.getByLabelText(/choose candidate document/i), {
      target: {
        files: [
          new File(["%PDF-1.7 synthetic"], "letter.pdf", {
            type: "application/pdf",
          }),
        ],
      },
    });
    const upload = screen.getByRole("button", { name: /upload document/i });
    fireEvent.click(upload);
    fireEvent.click(upload);
    expect(screen.getByRole("button", { name: /uploading/i })).toBeDisabled();
    expect(requester).toHaveBeenCalledTimes(2);

    resolveUpload(response(document, 201));
    await waitFor(() => expect(requester).toHaveBeenCalledTimes(3));
  });

  it.each([
    ["enroll", "Set up MFA to access documents"],
    ["verify", "Verify with MFA to access documents"],
  ] as const)(
    "offers the bounded %s path before making a private document request",
    async (mfaState, action) => {
      const requester = vi.fn();
      const { CandidateDocuments } = await import(
        "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
      );
      render(
        <CandidateDocuments
          applicationId={applicationId}
          applicationState="submitted"
          applicationStatus="application_submitted"
          requester={requester}
          inspectMfa={() => Promise.resolve(mfaState)}
        />,
      );
      expect(await screen.findByRole("link", { name: action })).toHaveAttribute(
        "href",
        `/auth/mfa?returnTo=%2Fcandidate%2Fapplications%2F${applicationId}%23documents`,
      );
      expect(requester).not.toHaveBeenCalled();
    },
  );

  it("maps an automatic document AAL denial back to a verification action", async () => {
    const requester = vi.fn().mockResolvedValue(response({}, 403));
    const { CandidateDocuments } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
    );
    render(
      <CandidateDocuments
        applicationId={applicationId}
        applicationState="submitted"
        applicationStatus="application_submitted"
        requester={requester}
        inspectMfa={() => Promise.resolve("aal2")}
      />,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(/mfa step-up/i);
    expect(
      screen.getByRole("link", { name: /verify with mfa/i }),
    ).toBeInTheDocument();
    expect(requester).toHaveBeenCalledOnce();
  });

  it.each([
    [422, "unsupported_extension", /file type is not supported/i],
    [422, "declared_mime_mismatch", /reported by your browser/i],
    [422, "detected_mime_mismatch", /contents do not match/i],
    [422, "pdf_structure_invalid", /pdf could not be read safely/i],
    [422, "docx_structure_invalid", /docx could not be read safely/i],
    [422, "legacy_doc_invalid", /doc could not be read safely/i],
    [422, "file_too_large", /larger than 10 mib/i],
    [422, "malware_detected", /failed its security scan/i],
    [
      503,
      "scanner_unavailable",
      /security scanning is temporarily unavailable/i,
    ],
    [503, "storage_unavailable", /storage is temporarily unavailable/i],
  ])(
    "shows a bounded upload error category for %s %s",
    async (status, detail, message) => {
      const requester = vi
        .fn()
        .mockResolvedValueOnce(response({ items: [] }))
        .mockResolvedValueOnce(response({ detail }, status));
      const { CandidateDocuments } = await import(
        "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
      );
      render(
        <CandidateDocuments
          applicationId={applicationId}
          applicationState="draft"
          applicationStatus="application_started"
          requester={requester}
          inspectMfa={() => Promise.resolve("aal2")}
        />,
      );
      await screen.findByText("No documents uploaded yet.");
      fireEvent.change(screen.getByLabelText(/choose candidate document/i), {
        target: {
          files: [
            new File(["%PDF-1.7 synthetic"], "letter.pdf", {
              type: "application/pdf",
            }),
          ],
        },
      });
      fireEvent.click(screen.getByRole("button", { name: /upload document/i }));
      expect(await screen.findByRole("alert")).toHaveTextContent(message);
    },
  );

  it("bounds MFA inspection failure and retries only on user action", async () => {
    const requester = vi.fn();
    const inspectMfa = vi
      .fn()
      .mockRejectedValueOnce(new Error("provider payload"))
      .mockResolvedValueOnce("enroll");
    const { CandidateDocuments } = await import(
      "@/app/(candidate)/candidate/applications/[applicationId]/candidate-documents"
    );
    render(
      <CandidateDocuments
        applicationId={applicationId}
        applicationState="draft"
        applicationStatus="application_started"
        requester={requester}
        inspectMfa={inspectMfa}
      />,
    );
    expect(await screen.findByRole("alert")).not.toHaveTextContent(
      /provider payload/i,
    );
    expect(inspectMfa).toHaveBeenCalledOnce();
    fireEvent.click(
      screen.getByRole("button", { name: /try security check again/i }),
    );
    expect(
      await screen.findByRole("link", { name: /set up mfa/i }),
    ).toBeInTheDocument();
    expect(inspectMfa).toHaveBeenCalledTimes(2);
    expect(requester).not.toHaveBeenCalled();
  });
});
