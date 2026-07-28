import { describe, expect, it } from "vitest";
import { hydrateBorrowerDraft } from "@/app/(borrower)/mortgage-application/draft-hydration";

describe("borrower draft hydration", () => {
  it("restores every non-SIN section and resumes at the last populated section so saved answers stay visible", () => {
    const restored = hydrateBorrowerDraft({
      mortgage_request: {
        mortgage_objective: "purchase",
        requested_amount: "425000.00",
        estimated_property_value: "550000.00",
        expected_closing_date: "2026-10-15",
        down_payment_sources: [
          { source: "savings", amount: "50000.00", description: "Saved" },
        ],
      },
      primary_borrower: {
        first_name: "Synthetic",
        sin: "must-not-hydrate",
        current_address: {
          street: "10 Example Street",
          city: "Toronto",
          province: "ON",
          postal_code: "M5V2T6",
          years_at_address: 2,
          months_at_address: 3,
        },
        employment: [
          {
            employment_type: "employed",
            occupation_category: "technology",
            industry: "software",
            duration_years: 4,
            duration_months: 2,
            annual_gross_income: "100000.00",
          },
        ],
      },
      co_borrower: {
        first_name: "Synthetic Co-borrower",
        sin: "must-also-not-hydrate",
        relationship_to_primary: "Spouse",
        employment: [],
      },
      assets: [{ asset_type: "savings", value: "75000.00" }],
      assets_complete: true,
      liabilities: [
        {
          liability_type: "car_loan",
          current_balance: "10000.00",
          payment_amount: "350.00",
          payment_frequency: "monthly",
        },
      ],
      liabilities_complete: true,
      subject_property: {
        address: "20 Property Street",
        city: "Toronto",
        province: "ON",
        postal_code: "M5V2T6",
        property_type: "single_family",
        property_style: "detached",
        occupancy: "owner_occupied",
      },
      other_properties: [
        {
          address: "30 Other Street",
          purchase_price: "300000.00",
          estimated_value: "425000.00",
          is_owner_occupied: false,
          mortgages: [
            {
              balance: "200000.00",
              payment_amount: "1200.00",
              payment_frequency: "monthly",
            },
          ],
        },
      ],
      additional_notes: "Synthetic testing note.",
    });

    expect(restored.mortgage.requested_amount).toBe("425000.00");
    expect(restored.mortgage.down_payment_sources[0]?.amount).toBe("50000.00");
    expect(restored.primary.first_name).toBe("Synthetic");
    expect(restored.primary.sin).toBe("");
    expect(restored.coBorrower?.first_name).toBe("Synthetic Co-borrower");
    expect(restored.coBorrower?.sin).toBe("");
    expect(restored.primaryEmployment[0]?.annual_gross_income).toBe(
      "100000.00",
    );
    expect(restored.assets[0]?.value).toBe("75000.00");
    expect(restored.assetsComplete).toBe(true);
    expect(restored.liabilities[0]?.current_balance).toBe("10000.00");
    expect(restored.liabilitiesComplete).toBe(true);
    expect(restored.subjectProperty.address).toBe("20 Property Street");
    expect(restored.subjectProperty.property_style).toBe("detached");
    expect(restored.otherProperties[0]?.mortgages[0]?.balance).toBe(
      "200000.00",
    );
    expect(restored.notes).toBe("Synthetic testing note.");
    expect(restored.resumeStep).toBe(6);
  });
});
