import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { BorrowerApplicationForm } from "@/app/(borrower)/mortgage-application/borrower-application-form";
import { BorrowerDetailsSection } from "@/app/(borrower)/mortgage-application/components/borrower-details-section";
import { ConsentSection } from "@/app/(borrower)/mortgage-application/components/consent-section";
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
    render(<ConsentSection acknowledged={false} onChange={vi.fn()} />);
    expect(
      screen.getByText(/synthetic-local-borrower-consent/),
    ).toBeInTheDocument();
    expect(document.body.textContent).toContain("not a signature");
    expect(document.body.textContent).not.toMatch(/typed name/i);
    expect(screen.getAllByRole("checkbox")).toHaveLength(1);
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
    ).toEqual(["owner_occupied", "tenant", "vacant", "other"]);
    expect(occupancy).not.toHaveTextContent("Second home");
    expect(occupancy).not.toHaveTextContent("second_home");

    const propertyStyle = screen.getByLabelText("Property style (required)");
    expect(propertyStyle.tagName).toBe("SELECT");
    expect(
      Array.from(propertyStyle.querySelectorAll("option")).map(
        (option) => option.value,
      ),
    ).toEqual([
      "detached",
      "semi_detached",
      "townhouse_row",
      "apartment",
      "other",
    ]);
  });

  it("has no browser-persistence, analytics, console, or submission code path for answers", () => {
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
    expect(clientSource).not.toMatch(/borrower-applications\/[^"]*submit/);
  });
});
