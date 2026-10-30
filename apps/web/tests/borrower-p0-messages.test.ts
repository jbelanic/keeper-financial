import { describe, expect, it } from "vitest";
import {
  numberChecks,
  numberIssueMessage,
  numberValue,
  parseNumberInput,
} from "@/lib/number-input";
import {
  humaniseIssueMessage,
  issueFieldLabel,
  issueSummary,
} from "@/lib/borrower-issue-messages";
import { uploadFailureMessage } from "@/lib/upload-messages";
import { BorrowerApplicationError } from "@/lib/borrower-application-api";

describe("amount entry", () => {
  it("reads the way people type money", () => {
    expect(numberValue("650,000")).toBe(650000);
    expect(numberValue("$650,000")).toBe(650000);
    expect(numberValue("650000")).toBe(650000);
    expect(numberValue(" 650 000.50 ")).toBe(650000.5);
    expect(numberValue("650,000.00")).toBe(650000);
    expect(numberValue(".5")).toBe(0.5);
  });

  it("treats an untouched field as empty rather than zero", () => {
    expect(numberValue("")).toBeUndefined();
    expect(parseNumberInput("   ").state).toBe("empty");
  });

  it("refuses text and excess precision instead of dropping the value", () => {
    expect(parseNumberInput("about 650k")).toEqual({
      state: "invalid",
      reason: "format",
    });
    expect(parseNumberInput("650,000.123")).toEqual({
      state: "invalid",
      reason: "precision",
    });
    expect(numberValue("-500")).toBeUndefined();
  });

  it("holds whole numbers to whole values", () => {
    expect(numberValue("2", "integer")).toBe(2);
    expect(numberValue("2.5", "integer")).toBeUndefined();
    expect(numberValue("2,000", "integer")).toBe(2000);
  });
});

describe("amount messages", () => {
  it("names the field and shows an example", () => {
    expect(
      numberIssueMessage("Requested mortgage amount", "money", "format"),
    ).toBe(
      "Requested mortgage amount must be an amount, for example 650000 or 650,000.",
    );
    expect(numberIssueMessage("Number of units", "integer", "format")).toBe(
      "Number of units must be a whole number, for example 2.",
    );
    expect(
      numberIssueMessage("Monthly property tax", "money", "precision"),
    ).toBe("Monthly property tax can have at most two decimal places.");
  });

  it("reports every rejected amount in one section", () => {
    expect(
      numberChecks([
        { label: "Requested mortgage amount", raw: "abc" },
        { label: "Estimated property value", raw: "850,000" },
      ]),
    ).toEqual([
      "Requested mortgage amount must be an amount, for example 650000 or 650,000.",
    ]);
  });
});

describe("validation messages", () => {
  it("turns library wording into an instruction", () => {
    expect(
      humaniseIssueMessage("Value error, must be a valid email address"),
    ).toBe("Enter a valid email address, for example name@example.com.");
    expect(
      humaniseIssueMessage(
        "Value error, must be a valid North American phone number",
      ),
    ).toBe("Enter a 10-digit phone number, for example (519) 123-4567.");
    expect(
      humaniseIssueMessage("String should have at least 6 characters"),
    ).toBe("Enter at least 6 characters.");
    expect(
      humaniseIssueMessage("Value error, SIN failed Luhn validation"),
    ).toContain("not a valid SIN");
  });

  it("never repeats an internal field path", () => {
    const summary = issueSummary({
      path: ["body", "primary_borrower", "current_address", "postal_code"],
      message: "String should have at least 6 characters",
    });
    expect(summary).toBe("Postal code: Enter at least 6 characters.");
    expect(summary).not.toContain("primary_borrower");
    expect(summary).not.toContain("Value error");
  });

  it("labels the field from the deepest known path segment", () => {
    expect(
      issueFieldLabel(["body", "mortgage_request", "requested_amount"]),
    ).toBe("Requested mortgage amount");
    expect(issueFieldLabel(["body", "assets", 0, "value"])).toBe("Asset value");
    expect(issueFieldLabel([])).toBe("This answer");
  });
});

describe("upload refusal messages", () => {
  it("explains a damaged PDF in the applicant's terms", () => {
    expect(
      uploadFailureMessage(
        new BorrowerApplicationError(422, [], "pdf_structure_invalid"),
      ),
    ).toMatch(/could not be read/i);
  });

  it("explains limits, scanning and outages distinctly", () => {
    expect(
      uploadFailureMessage(
        new BorrowerApplicationError(413, [], "file_too_large"),
      ),
    ).toMatch(/25 MB/);
    expect(
      uploadFailureMessage(
        new BorrowerApplicationError(422, [], "malware_detected"),
      ),
    ).toMatch(/virus scan/i);
    expect(uploadFailureMessage(new BorrowerApplicationError(503))).toMatch(
      /nothing was uploaded/i,
    );
  });

  it("falls back to a sentence that promises no silent success", () => {
    expect(uploadFailureMessage(new Error("boom"))).toMatch(
      /nothing was added/i,
    );
  });
});
