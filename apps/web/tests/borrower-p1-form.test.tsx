import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { BorrowerApplicationForm } from "@/app/(borrower)/mortgage-application/borrower-application-form";
import { SubjectPropertySection } from "@/app/(borrower)/mortgage-application/components/subject-property-section";
import { AssetsLiabilitiesSection } from "@/app/(borrower)/mortgage-application/components/assets-liabilities-section";
import { OtherPropertiesSection } from "@/app/(borrower)/mortgage-application/components/other-properties-section";
import { emptyOtherProperty } from "@/app/(borrower)/mortgage-application/components/types";
import {
  isValidEmail,
  isValidPostalCode,
  normalizePostalCode,
  passesSinChecksum,
} from "@/lib/validation";

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

function fillBorrower(overrides: {
  sin?: string;
  email?: string;
  postal?: string;
}) {
  fireEvent.change(screen.getByLabelText("Legal first name (required)"), {
    target: { value: "Jordan" },
  });
  fireEvent.change(screen.getByLabelText("Legal last name (required)"), {
    target: { value: "Sinclair" },
  });
  fireEvent.change(screen.getByLabelText("Email (required)"), {
    target: { value: overrides.email ?? "jordan.sinclair@example.test" },
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
    target: { value: overrides.sin ?? "046454286" },
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
    target: { value: overrides.postal ?? "N6H 4T6" },
  });
  fireEvent.change(screen.getByLabelText("Number of dependants (required)"), {
    target: { value: "0" },
  });
  fireEvent.change(screen.getByLabelText("Years at address (required)"), {
    target: { value: "3" },
  });
  fireEvent.change(screen.getByLabelText("Additional months (required)"), {
    target: { value: "2" },
  });
}

async function openBorrowerStep(patch = vi.fn().mockResolvedValue(saved)) {
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
  await screen.findByRole("heading", { name: "Borrowers" });
  // Reset so an assertion about the borrower section sees only its own save.
  patch.mockClear();
  return patch;
}

describe("client-side format rules mirror the API", () => {
  it("validates email, postal code and the SIN checksum", () => {
    expect(isValidEmail("jordan@example.test")).toBe(true);
    expect(isValidEmail("jordan@")).toBe(false);
    expect(isValidPostalCode("N6H 4T6")).toBe(true);
    expect(isValidPostalCode("n6h4t6")).toBe(true);
    expect(isValidPostalCode("12345")).toBe(false);
    expect(normalizePostalCode(" n6h  4t6 ")).toBe("N6H4T6");
    // Both are issued-format 9-digit values; only the second passes Luhn.
    expect(passesSinChecksum("046454286")).toBe(true);
    expect(passesSinChecksum("123456789")).toBe(false);
    expect(passesSinChecksum("04645428")).toBe(false);
  });
});

describe("borrower details catch format mistakes before saving", () => {
  it("refuses a SIN that fails the checksum without calling the API", async () => {
    const patch = await openBorrowerStep();
    fillBorrower({ sin: "123456789" });
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    // Inline under the field and repeated in the summary, so match either.
    expect(
      (await screen.findAllByText(/fails its own check digit/i)).length,
    ).toBeGreaterThan(0);
    expect(patch).not.toHaveBeenCalled();
    const sin = screen.getByLabelText(/Social Insurance Number/);
    expect(sin).toHaveValue("123456789");
    expect(sin).toHaveAttribute("aria-invalid", "true");
  });

  it("names the postal code and email problems instead of sending them", async () => {
    const patch = await openBorrowerStep();
    fillBorrower({ postal: "12345", email: "jordan@" });
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    expect(
      (await screen.findAllByText(/that email address is not complete/i))
        .length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/enter a Canadian postal code, for example N6H 4T6/i)
        .length,
    ).toBeGreaterThan(0);
    expect(patch).not.toHaveBeenCalled();
  });

  it("discloses the SIN checksum in the field hint", async () => {
    await openBorrowerStep();
    expect(screen.getByText(/checksummed/i)).toBeInTheDocument();
  });
});

describe("selects replace free text where the vocabulary is fixed", () => {
  it("offers the province list on the subject property", () => {
    render(
      <SubjectPropertySection
        value={{
          identified: true,
          address: "",
          city: "",
          province: "",
          postal_code: "",
          property_type: "",
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
        }}
        onChange={vi.fn()}
      />,
    );
    const province = screen.getByLabelText("Province or territory (required)");
    expect(province.tagName).toBe("SELECT");
    expect(
      Array.from(province.querySelectorAll("option")).map((o) => o.value),
    ).toEqual([
      "",
      "AB",
      "BC",
      "MB",
      "NB",
      "NL",
      "NS",
      "NT",
      "NU",
      "ON",
      "PE",
      "QC",
      "SK",
      "YT",
    ]);
  });

  it("offers a payment-frequency list on a liability", () => {
    render(
      <AssetsLiabilitiesSection
        assets={[]}
        liabilities={[
          {
            id: "liability-1",
            liability_type: "credit_card",
            current_balance: "3400",
            payment_amount: "150",
            payment_frequency: "",
            description: "",
          },
        ]}
        assetsComplete
        liabilitiesComplete
        onAssetsChange={vi.fn()}
        onLiabilitiesChange={vi.fn()}
        onAssetsCompleteChange={vi.fn()}
        onLiabilitiesCompleteChange={vi.fn()}
      />,
    );
    const frequency = screen.getByLabelText("Payment frequency (optional)");
    expect(frequency.tagName).toBe("SELECT");
    expect(
      Array.from(frequency.querySelectorAll("option")).map((o) => o.value),
    ).toEqual(["", "monthly", "semi_monthly", "bi_weekly", "weekly", "annual"]);
  });

  it("keeps a saved frequency that is not in the list rather than dropping it", () => {
    render(
      <AssetsLiabilitiesSection
        assets={[]}
        liabilities={[
          {
            id: "liability-1",
            liability_type: "credit_card",
            current_balance: "3400",
            payment_amount: "150",
            payment_frequency: "quarterly",
            description: "",
          },
        ]}
        assetsComplete
        liabilitiesComplete
        onAssetsChange={vi.fn()}
        onLiabilitiesChange={vi.fn()}
        onAssetsCompleteChange={vi.fn()}
        onLiabilitiesCompleteChange={vi.fn()}
      />,
    );
    const frequency = screen.getByLabelText(
      "Payment frequency (optional)",
    ) as HTMLSelectElement;
    expect(frequency.value).toBe("quarterly");
    expect(frequency).toHaveTextContent("quarterly");
  });

  it("marks every other-property field required or optional", () => {
    render(
      <OtherPropertiesSection
        properties={[emptyOtherProperty()]}
        onChange={vi.fn()}
      />,
    );
    expect(
      screen.getByLabelText("Property address (optional)"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Purchase date (optional)"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Purchase price (optional)"),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Estimated value (optional)"),
    ).toBeInTheDocument();
  });
});
