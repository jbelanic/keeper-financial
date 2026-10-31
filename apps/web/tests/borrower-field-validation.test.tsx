import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { BorrowerApplicationForm } from "@/app/(borrower)/mortgage-application/borrower-application-form";
import { validateEmploymentEntries } from "@/app/(borrower)/mortgage-application/section-validation";
import {
  emptyEmployment,
  type EmploymentState,
} from "@/app/(borrower)/mortgage-application/components/types";

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

function fillMortgage() {
  fireEvent.change(screen.getByLabelText("Mortgage purpose (required)"), {
    target: { value: "purchase" },
  });
  fireEvent.change(screen.getByLabelText("Requested mortgage amount"), {
    target: { value: "650000" },
  });
}

function fillBorrower() {
  const changes: Array<[string | RegExp, string]> = [
    ["Legal first name (required)", "Jordan"],
    ["Legal last name (required)", "Sinclair"],
    ["Email (required)", "jordan.sinclair@example.test"],
    ["Phone (required)", "519-123-4567"],
    ["Preferred contact method (required)", "email"],
    ["Date of birth (required)", "1985-06-12"],
    [/Social Insurance Number/, "046454286"],
    ["Marital status (required)", "married"],
    ["Street address (required)", "123 Maple Grove Avenue"],
    ["City (required)", "London"],
    ["Province or territory (required)", "ON"],
    ["Postal code (required)", "N6H 4T6"],
    ["Number of dependants (required)", "0"],
    ["Years at address (required)", "3"],
    ["Additional months (required)", "2"],
  ];
  for (const [label, value] of changes) {
    fireEvent.change(screen.getByLabelText(label), { target: { value } });
  }
}

async function openEmploymentStep() {
  const patch = vi.fn().mockResolvedValue(saved);
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
  fillMortgage();
  fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));
  await screen.findByRole("heading", { name: "Borrowers" });
  fillBorrower();
  fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));
  await screen.findByRole("heading", { name: "Employment and income" });
  patch.mockClear();
  return patch;
}

describe("employment validation names the field, not just the entry", () => {
  const entry: EmploymentState = { ...emptyEmployment() };

  it("reports each missing field separately with its own control id", () => {
    const issues = validateEmploymentEntries("primary", "Primary borrower", [
      entry,
    ]);
    const fields = issues.map((issue) => issue.field);

    expect(fields).toEqual(
      expect.arrayContaining([
        `primary-employment-type-${entry.id}`,
        `primary-occupation-${entry.id}`,
        `primary-industry-${entry.id}`,
        `primary-income-${entry.id}`,
      ]),
    );
    // The entry starts at 0 years / 0 months, which satisfies the API.
    expect(fields).not.toContain(`primary-duration-years-${entry.id}`);
    for (const issue of issues) {
      expect(issue.message).not.toMatch(/missing a required value/i);
      expect(issue.message.length).toBeGreaterThan(15);
    }
    const income = issues.find(
      (issue) => issue.field === `primary-income-${entry.id}`,
    );
    expect(income?.label).toBe(
      "Primary borrower income entry 1 — annual gross income",
    );
    expect(income?.message).toMatch(/annual gross income/i);
  });

  it("marks the offending control and puts the message under it", async () => {
    const patch = await openEmploymentStep();

    fireEvent.change(
      screen.getByLabelText("Employment or income type (required)"),
      {
        target: { value: "employed" },
      },
    );
    fireEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    const income = screen.getByLabelText("Annual gross income (required)");
    expect(income).toHaveAttribute("aria-invalid", "true");
    expect(income.getAttribute("aria-describedby")).toMatch(/-error$/);
    expect(income.closest(".form-field")?.textContent).toMatch(
      /enter the annual gross income before deductions/i,
    );

    const industry = screen.getByLabelText("Industry (required)");
    expect(industry).toHaveAttribute("aria-invalid", "true");
    expect(industry.closest(".form-field")?.textContent).toMatch(
      /enter the industry, for example residential construction/i,
    );

    // The summary names the section, the borrower, the field and the fix.
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toMatch(
      /Primary borrower income entry 1 .* annual gross income: Enter the annual gross income before deductions/,
    );
    expect(alert.textContent).not.toMatch(/missing a required value/i);
    expect(patch).not.toHaveBeenCalled();
  });
});
