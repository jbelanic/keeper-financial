import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BorrowerApplicationForm } from "@/app/(borrower)/mortgage-application/borrower-application-form";
import { DocumentUpload } from "@/app/(borrower)/mortgage-application/components/document-upload";
import { BorrowerApplicationError } from "@/lib/borrower-application-api";

const applicationId = "11111111-1111-4111-8111-111111111111";
const started = {
  application_id: applicationId,
  revision: 0,
  lifecycle_status: "draft",
};
const saved = {
  ...started,
  revision: 1,
  has_sin: false,
  has_co_borrower: false,
  last_activity_at: "2026-07-25T12:00:00Z",
  draft_expires_at: "2026-08-24T12:00:00Z",
};
const consent = {
  consent_version: "borrower-privacy-credit-disclosure-2026-07-27-v1",
  wording_digest: "a".repeat(64),
  wording_text: "Synthetic privacy and credit-use wording for tests.",
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

async function openForm(
  api: Parameters<typeof BorrowerApplicationForm>[0]["api"],
) {
  render(<BorrowerApplicationForm api={api} />);
  await screen.findByRole("heading", { name: "Mortgage application" });
}

function fillRequiredBorrowerFields() {
  fireEvent.change(screen.getByLabelText("Legal first name (required)"), {
    target: { value: "Jordan" },
  });
  fireEvent.change(screen.getByLabelText("Legal last name (required)"), {
    target: { value: "Sinclair" },
  });
  fireEvent.change(screen.getByLabelText("Email (required)"), {
    target: { value: "jordan.sinclair@example.test" },
  });
  fireEvent.change(screen.getByLabelText("Phone (required)"), {
    target: { value: "519-123-4567" },
  });
  fireEvent.change(
    screen.getByLabelText("Preferred contact method (required)"),
    {
      target: { value: "email" },
    },
  );
  fireEvent.change(screen.getByLabelText("Date of birth (required)"), {
    target: { value: "1985-06-12" },
  });
  fireEvent.change(screen.getByLabelText(/Social Insurance Number/), {
    target: { value: "046454286" },
  });
  fireEvent.change(screen.getByLabelText("Marital status (required)"), {
    target: { value: "married" },
  });
  fireEvent.change(screen.getByLabelText("Street address (required)"), {
    target: { value: "123 Maple Grove Avenue" },
  });
  fireEvent.change(screen.getByLabelText("City (required)"), {
    target: { value: "London" },
  });
  fireEvent.change(screen.getByLabelText("Province or territory (required)"), {
    target: { value: "ON" },
  });
  fireEvent.change(screen.getByLabelText("Postal code (required)"), {
    target: { value: "N6H 4T6" },
  });
}

describe("amount entry in the borrower application", () => {
  it("saves a comma-formatted amount as the number the applicant meant", async () => {
    const patch = vi.fn().mockResolvedValue(saved);
    await openForm({
      recoverOrStart: vi
        .fn()
        .mockResolvedValue({ draft: started, recovered: false }),
      patch,
    });

    fireEvent.change(screen.getByLabelText("Mortgage purpose (required)"), {
      target: { value: "purchase" },
    });
    fireEvent.change(screen.getByLabelText("Requested mortgage amount"), {
      target: { value: "650,000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith(applicationId, 0, {
        mortgage_request: {
          mortgage_objective: "purchase",
          requested_amount: 650000,
          down_payment_sources: [],
        },
      }),
    );
  });

  it("refuses an amount it cannot read instead of saving a section without it", async () => {
    const patch = vi.fn().mockResolvedValue(saved);
    await openForm({
      recoverOrStart: vi
        .fn()
        .mockResolvedValue({ draft: started, recovered: false }),
      patch,
    });

    fireEvent.change(screen.getByLabelText("Mortgage purpose (required)"), {
      target: { value: "purchase" },
    });
    fireEvent.change(screen.getByLabelText("Requested mortgage amount"), {
      target: { value: "about 650k" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    expect(
      await screen.findByText(
        "Requested mortgage amount must be an amount, for example 650000 or 650,000.",
      ),
    ).toBeInTheDocument();
    expect(patch).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Requested mortgage amount")).toHaveValue(
      "about 650k",
    );
  });
});

describe("validation messages in the borrower application", () => {
  it("shows a server rejection beside the field, without internal paths", async () => {
    const patch = vi
      .fn()
      .mockResolvedValueOnce(saved)
      .mockRejectedValueOnce(
        new BorrowerApplicationError(422, [
          {
            path: [
              "body",
              "primary_borrower",
              "current_address",
              "postal_code",
            ],
            message: "String should have at least 6 characters",
          },
        ]),
      );
    await openForm({
      recoverOrStart: vi
        .fn()
        .mockResolvedValue({ draft: started, recovered: false }),
      patch,
    });

    fireEvent.change(screen.getByLabelText("Mortgage purpose (required)"), {
      target: { value: "pre_approval" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await screen.findByRole("heading", { name: "Borrowers" });

    fillRequiredBorrowerFields();
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    expect(
      await screen.findByText("Postal code: Enter at least 6 characters."),
    ).toBeInTheDocument();
    const postal = screen.getByLabelText("Postal code (required)");
    expect(postal).toHaveAttribute("aria-invalid", "true");
    expect(postal.getAttribute("aria-describedby")).toContain(
      "primary-postal-error",
    );
    expect(document.body.textContent).not.toMatch(
      /primary_borrower|Value error/,
    );
    expect(screen.getByLabelText("Postal code (required)")).toHaveValue(
      "N6H 4T6",
    );
  });
});

describe("document upload refusals", () => {
  it("says why the file was refused and keeps the saved list on screen", async () => {
    const existing = {
      document_id: "22222222-2222-4222-8222-222222222222",
      filename: "pay-stub.pdf",
      category: "income_employment",
      description: null,
      mime_type: "application/pdf",
      size_bytes: 2048,
      scan_status: "clean",
      uploaded_at: "2026-07-25T12:00:00Z",
    };
    const fetcher = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ items: [existing], total: 1 }))
      .mockResolvedValueOnce(
        jsonResponse({ detail: "pdf_structure_invalid" }, 422),
      )
      .mockResolvedValueOnce(jsonResponse({ items: [existing], total: 1 }));

    render(
      <DocumentUpload
        applicationId={applicationId}
        onSettledChange={vi.fn()}
      />,
    );
    await screen.findByText(/1 document on this application/);

    fireEvent.change(
      screen.getByLabelText("Select a PDF, DOC, DOCX, JPEG, or PNG"),
      { target: { files: [new File(["damaged"], "damaged.pdf")] } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Upload document" }));

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/could not be read/i);
    expect(screen.getAllByText(/pay-stub\.pdf/).length).toBeGreaterThan(0);
    expect(fetcher).toHaveBeenCalledTimes(3);
  });
});

describe("submission completeness", () => {
  it("names the section that blocks submission instead of sending the request", async () => {
    const submit = vi.fn();
    const recoveredDraft = {
      ...saved,
      has_sin: true,
      payload: {
        mortgage_request: {
          mortgage_objective: "purchase",
          requested_amount: "650000.00",
        },
        primary_borrower: {
          first_name: "Jordan",
          last_name: "Sinclair",
          email: "jordan.sinclair@example.test",
          preferred_contact_method: "email",
          date_of_birth: "1985-06-12",
          marital_status: "married",
          number_of_dependants: 0,
          current_address: {
            street: "123 Maple Grove Avenue",
            city: "London",
            province: "ON",
            postal_code: "N6H4T6",
            years_at_address: 5,
            months_at_address: 3,
          },
          employment: [
            {
              employment_type: "employed",
              occupation_category: "Operations analyst",
              industry: "Information technology",
              duration_years: 4,
              duration_months: 6,
              annual_gross_income: "92000.00",
            },
          ],
        },
        assets_complete: true,
        liabilities_complete: true,
        subject_property: null,
        other_properties: [],
        additional_notes: "Synthetic note.",
      },
    };
    vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      jsonResponse({ items: [] }),
    );

    await openForm({
      recoverOrStart: vi
        .fn()
        .mockResolvedValue({ draft: recoveredDraft, recovered: true }),
      patch: vi.fn().mockResolvedValue({ ...recoveredDraft, revision: 2 }),
      getConsent: vi.fn().mockResolvedValue(consent),
      submit,
    });

    await screen.findByText(/Existing private draft recovered/i);
    // The recovered draft lands on its highest populated section (Notes).
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    fireEvent.click(
      await screen.findByRole("button", { name: "Continue to consent" }),
    );
    fireEvent.click(screen.getByLabelText(/acknowledge the privacy/i));
    fireEvent.click(screen.getByRole("button", { name: "Submit application" }));

    expect(
      await screen.findByRole("heading", {
        name: "Finish these sections before submitting",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Borrowers: Primary borrower: phone is required\./),
    ).toBeInTheDocument();
    expect(submit).not.toHaveBeenCalled();
  });
});
