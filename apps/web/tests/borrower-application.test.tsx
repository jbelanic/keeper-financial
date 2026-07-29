import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import {
  BorrowerApplicationForm,
  validateSubjectProperty,
} from "@/app/(borrower)/mortgage-application/borrower-application-form";
import { BorrowerDetailsSection } from "@/app/(borrower)/mortgage-application/components/borrower-details-section";
import { ConsentSection } from "@/app/(borrower)/mortgage-application/components/consent-section";
import { DocumentUpload } from "@/app/(borrower)/mortgage-application/components/document-upload";
import { SubjectPropertySection } from "@/app/(borrower)/mortgage-application/components/subject-property-section";
import { emptyBorrower } from "@/app/(borrower)/mortgage-application/components/types";
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

describe("accountless borrower application form", () => {
  it("starts a draft, saves a section revision, and advances only after success", async () => {
    const recoverOrStart = vi
      .fn()
      .mockResolvedValue({ draft: started, recovered: false });
    const patch = vi.fn().mockResolvedValue(saved);
    render(
      <BorrowerApplicationForm
        preferredAgentSlug="published-agent"
        api={{ recoverOrStart, patch }}
      />,
    );

    expect(
      await screen.findByRole("heading", { name: "Mortgage application" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByText("Same-browser private draft"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Save one section at a time/i),
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(/Your draft is saved section by section/i),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Mortgage purpose (required)"), {
      target: { value: "purchase" },
    });
    fireEvent.change(screen.getByLabelText("Requested mortgage amount"), {
      target: { value: "250000" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith(applicationId, 0, {
        mortgage_request: {
          mortgage_objective: "purchase",
          requested_amount: 250000,
          preferred_agent_slug: "published-agent",
          down_payment_sources: [],
        },
      }),
    );
    expect(
      await screen.findByRole("heading", { name: "Borrowers" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Section saved securely.")).toBeInTheDocument();
  });

  it("preserves the current step and visible values on a server failure", async () => {
    const patch = vi.fn().mockRejectedValue(new BorrowerApplicationError(503));
    render(
      <BorrowerApplicationForm
        api={{
          recoverOrStart: vi
            .fn()
            .mockResolvedValue({ draft: started, recovered: false }),
          patch,
        }}
      />,
    );
    await screen.findByRole("heading", { name: "Mortgage application" });
    fireEvent.change(screen.getByLabelText("Mortgage purpose (required)"), {
      target: { value: "pre_approval" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await screen.findByRole("heading", {
      name: "This section was not saved",
    });
    expect(screen.getByRole("alert")).toHaveFocus();
    expect(
      screen.getByRole("heading", { name: "Mortgage request" }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Mortgage purpose (required)")).toHaveValue(
      "pre_approval",
    );
    expect(
      screen.getByText("Nothing was advanced or cleared."),
    ).toBeInTheDocument();
  });

  it("restores saved non-SIN answers from an authorized recovered draft", async () => {
    const recoveredDraft = {
      ...saved,
      has_sin: true,
      payload: {
        mortgage_request: {
          mortgage_objective: "purchase",
          requested_amount: "425000.00",
          estimated_property_value: "550000.00",
          expected_closing_date: "2026-10-15",
          preferred_agent_slug: "published-agent",
          down_payment_sources: [],
        },
        primary_borrower: {
          first_name: "Jamie",
          last_name: "Borrower",
          email: "jamie@example.test",
          phone: "14165550123",
          preferred_contact_method: "email",
          date_of_birth: "1990-01-01",
          marital_status: "single",
          number_of_dependants: 0,
          current_address: {
            street: "10 Example Street",
            city: "Toronto",
            province: "ON",
            postal_code: "M5V2T6",
            years_at_address: 2,
            months_at_address: 3,
          },
          employment: [],
        },
      },
    };
    const patch = vi.fn().mockResolvedValue(saved);

    render(
      <BorrowerApplicationForm
        api={{
          recoverOrStart: vi.fn().mockResolvedValue({
            draft: recoveredDraft,
            recovered: true,
          }),
          patch,
        }}
      />,
    );

    expect(
      await screen.findByText(
        "Existing private draft recovered. Saved non-SIN answers have been restored; SIN remains provided/masked only.",
      ),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^Mortgage request/ }));
    expect(screen.getByDisplayValue("425000.00")).toBeInTheDocument();
    expect(screen.getByLabelText("Mortgage purpose (required)")).toHaveValue(
      "purchase",
    );

    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    expect(await screen.findByDisplayValue("Jamie")).toBeInTheDocument();
    expect(screen.getByDisplayValue("jamie@example.test")).toBeInTheDocument();
    expect(
      screen.getByLabelText("Social Insurance Number (required)"),
    ).toHaveValue("");
  });

  it("does not claim restoration when a recovered draft has no payload", async () => {
    const recoveredDraft = {
      ...saved,
      has_sin: false,
      payload: null,
    };
    render(
      <BorrowerApplicationForm
        api={{
          recoverOrStart: vi
            .fn()
            .mockResolvedValue({ draft: recoveredDraft, recovered: true }),
          patch: vi.fn().mockResolvedValue(saved),
        }}
      />,
    );

    expect(
      await screen.findByText(
        "Saved draft found. No previous answers were restored yet; continue where you left off.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/Saved non-SIN answers have been restored/),
    ).not.toBeInTheDocument();
  });

  it("renders recovered SIN as provided state and never places it in the input", async () => {
    render(
      <BorrowerDetailsSection
        primary={emptyBorrower()}
        coBorrower={null}
        hasSavedPrimarySin
        hasSavedCoBorrower={false}
        onPrimaryChange={vi.fn()}
        onCoBorrowerChange={vi.fn()}
        onAddCoBorrower={vi.fn()}
        onRemoveCoBorrower={vi.fn()}
      />,
    );
    expect(screen.getByText(/SIN provided/)).toHaveTextContent("••• ••• •••");
    expect(
      screen.getByLabelText("Social Insurance Number (replace only)"),
    ).toHaveValue("");
    expect(document.body.textContent).not.toMatch(/\b\d{9}\b/);
  });

  it("adds at most one co-borrower with stable accessible controls", () => {
    const onAdd = vi.fn();
    const { rerender } = render(
      <BorrowerDetailsSection
        primary={emptyBorrower()}
        coBorrower={null}
        hasSavedPrimarySin={false}
        hasSavedCoBorrower={false}
        onPrimaryChange={vi.fn()}
        onCoBorrowerChange={vi.fn()}
        onAddCoBorrower={onAdd}
        onRemoveCoBorrower={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Add a co-borrower" }));
    expect(onAdd).toHaveBeenCalledOnce();

    rerender(
      <BorrowerDetailsSection
        primary={emptyBorrower()}
        coBorrower={emptyBorrower()}
        hasSavedPrimarySin={false}
        hasSavedCoBorrower={false}
        onPrimaryChange={vi.fn()}
        onCoBorrowerChange={vi.fn()}
        onAddCoBorrower={onAdd}
        onRemoveCoBorrower={vi.fn()}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Add a co-borrower" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByLabelText("Relationship to primary borrower (required)"),
    ).toBeInTheDocument();
  });

  it("shows versioned synthetic consent without marketing or signature UI", () => {
    render(
      <ConsentSection
        wording="Synthetic local borrower consent wording — not approved for real use."
        version="synthetic-local-borrower-consent"
        acknowledged={false}
        onChange={vi.fn()}
      />,
    );
    expect(
      screen.getByText(/synthetic-local-borrower-consent/),
    ).toBeInTheDocument();
    expect(document.body.textContent).toContain("not a signature");
    expect(document.body.textContent).not.toMatch(/typed name/i);
    expect(screen.getAllByRole("checkbox")).toHaveLength(1);
  });

  it("keeps document navigation unsettled until the current list loads", async () => {
    const onSettledChange = vi.fn();
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0 }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    render(
      <DocumentUpload
        applicationId={applicationId}
        onSettledChange={onSettledChange}
      />,
    );

    expect(onSettledChange).toHaveBeenCalledWith(false);
    await screen.findByText("No documents uploaded.");
    expect(onSettledChange).toHaveBeenLastCalledWith(true);
  });

  it("keeps document navigation blocked when the current list fails", async () => {
    const onSettledChange = vi.fn();
    vi.spyOn(globalThis, "fetch").mockRejectedValue(
      new Error("synthetic failure"),
    );

    render(
      <DocumentUpload
        applicationId={applicationId}
        onSettledChange={onSettledChange}
      />,
    );

    await screen.findByText("Documents could not be loaded. Try again.");
    expect(onSettledChange).toHaveBeenCalledWith(false);
    expect(onSettledChange).not.toHaveBeenCalledWith(true);
  });

  it("keeps document navigation blocked when a failed upload cannot be reconciled", async () => {
    const onSettledChange = vi.fn();
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ items: [], total: 0 }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockRejectedValueOnce(new Error("synthetic lost upload response"))
      .mockRejectedValueOnce(new Error("synthetic reconciliation failure"));

    render(
      <DocumentUpload
        applicationId={applicationId}
        onSettledChange={onSettledChange}
      />,
    );
    await screen.findByText("No documents uploaded.");
    fireEvent.change(
      screen.getByLabelText("Select a PDF, DOC, DOCX, JPEG, or PNG"),
      { target: { files: [new File(["safe"], "safe.pdf")] } },
    );
    fireEvent.click(screen.getByRole("button", { name: "Upload document" }));

    await screen.findByText(/could not be reconciled/i);
    expect(globalThis.fetch).toHaveBeenCalledTimes(3);
    expect(onSettledChange).toHaveBeenLastCalledWith(false);
  });

  it("renders subject-property selects with the API enum vocabularies only", () => {
    render(
      <SubjectPropertySection
        value={{
          identified: true,
          address: "",
          city: "",
          province: "",
          postal_code: "",
          property_type: "",
          property_style: "detached",
          occupancy: "owner_occupied",
          year_built: "",
          livable_area_sqft: "",
          units: "",
          monthly_property_tax: "",
          monthly_heating_cost: "",
          monthly_condo_fee: "",
          lot_details: "",
          garage_details: "",
        }}
        onChange={vi.fn()}
      />,
    );

    const occupancy = screen.getByLabelText("Occupancy (required)");
    expect(occupancy.tagName).toBe("SELECT");
    expect(
      Array.from(occupancy.querySelectorAll("option")).map(
        (option) => option.value,
      ),
    ).toEqual(["", "owner_occupied", "tenant", "vacant", "other"]);
    expect(occupancy).not.toHaveTextContent("Second home");
    expect(occupancy).not.toHaveTextContent("second_home");

    const propertyStyle = screen.getByLabelText("Property style (required)");
    expect(propertyStyle.tagName).toBe("SELECT");
    expect(
      Array.from(propertyStyle.querySelectorAll("option")).map(
        (option) => option.value,
      ),
    ).toEqual([
      "",
      "detached",
      "semi_detached",
      "townhouse_row",
      "apartment",
      "other",
    ]);
  });

  it("identifies every missing required subject-property field", () => {
    expect(
      validateSubjectProperty({
        identified: true,
        address: "1 Synthetic Street",
        city: "London",
        province: "ON",
        postal_code: "N6A 1A1",
        property_type: "single_family",
        property_style: "",
        occupancy: "",
        year_built: "",
        livable_area_sqft: "",
        units: "",
        monthly_property_tax: "",
        monthly_heating_cost: "",
        monthly_condo_fee: "",
        lot_details: "",
        garage_details: "",
      }),
    ).toEqual(["Property style is required.", "Occupancy is required."]);
  });

  it("has no answer persistence, analytics, console, or sensitive submission persistence", () => {
    const formSource = readFileSync(
      join(
        process.cwd(),
        "app/(borrower)/mortgage-application/borrower-application-form.tsx",
      ),
      "utf8",
    );
    const clientSource = readFileSync(
      join(process.cwd(), "lib/borrower-application-api.ts"),
      "utf8",
    );
    expect(formSource).not.toMatch(
      /localStorage|sessionStorage|console\.|window\.analytics|fetch\([^)]*submit/,
    );
    expect(clientSource).not.toMatch(
      /localStorage|console\.|window\.analytics/,
    );
    expect(clientSource).not.toContain("JSON.stringify(payload)");
    expect(clientSource).toContain("/submit");
  });
});
