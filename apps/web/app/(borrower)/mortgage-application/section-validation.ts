/**
 * Section validation for the borrower application.
 *
 * Every issue names the exact field it belongs to (`field` is the DOM id of the
 * control), carries the field's label for the summary, and carries a short
 * sentence written to sit directly under that control. Earlier versions
 * returned bare strings such as "Primary borrower income entry 2 is missing a
 * required value.", which named neither the field nor the entry the applicant
 * was supposed to fix, and gave the form nothing to highlight.
 */

import { isAcceptablePhoneInput } from "@/lib/phone";
import {
  numberFieldMessage,
  parseNumberInput,
  type NumberKind,
} from "@/lib/number-input";
import {
  isValidEmail,
  isValidPostalCode,
  passesSinChecksum,
} from "@/lib/validation";
import type {
  AssetState,
  BorrowerState,
  EmploymentState,
  LiabilityState,
  MortgageRequestState,
  OtherPropertyState,
  SubjectPropertyState,
} from "./components/types";

export type FieldIssue = {
  /** DOM id of the control to mark and to place the message under. */
  field: string;
  /** Field name with its context, used in the error summary. */
  label: string;
  /** One actionable sentence shown under the control. */
  message: string;
};

function missingText(
  field: string,
  label: string,
  value: string,
  message: string,
): FieldIssue[] {
  return value.trim() ? [] : [{ field, label, message }];
}

function missingChoice(
  field: string,
  label: string,
  value: string,
  message = "Choose one of the options.",
): FieldIssue[] {
  return value.trim() ? [] : [{ field, label, message }];
}

/** A whole number the API requires: empty is "missing", not "wrong format". */
function requiredNumber(
  field: string,
  label: string,
  raw: string,
  message: string,
  kind: NumberKind = "integer",
): FieldIssue[] {
  if (!raw.trim()) return [{ field, label, message }];
  return numberIssues(field, label, raw, kind);
}

function numberIssues(
  field: string,
  label: string,
  raw: string,
  kind: NumberKind = "money",
): FieldIssue[] {
  const parsed = parseNumberInput(raw, kind);
  return parsed.state === "invalid"
    ? [{ field, label, message: numberFieldMessage(kind, parsed.reason) }]
    : [];
}

export function validateMortgageRequest(
  value: MortgageRequestState,
): FieldIssue[] {
  const issues: FieldIssue[] = [
    ...missingChoice(
      "mortgage-objective",
      "Mortgage purpose",
      value.mortgage_objective,
      "Choose what you want to do — purchase, refinance, renew, or something else.",
    ),
  ];
  const needsAmount =
    ["purchase", "refinance"].includes(value.mortgage_objective) &&
    !value.requested_amount.trim() &&
    !value.estimated_property_value.trim();
  if (needsAmount) {
    issues.push({
      field: "requested-amount",
      label: "Requested mortgage amount",
      message:
        "Enter the amount you want to borrow, or the property value you are working from — one of the two is enough.",
    });
  }
  issues.push(
    ...numberIssues(
      "requested-amount",
      "Requested mortgage amount",
      value.requested_amount,
    ),
    ...numberIssues(
      "estimated-property-value",
      "Estimated property value",
      value.estimated_property_value,
    ),
  );
  value.down_payment_sources.forEach((source, index) => {
    const entry = `down-payment source ${index + 1}`;
    issues.push(
      ...missingChoice(
        `down-payment-source-${source.id}`,
        `${capitalise(entry)} — source`,
        source.source,
        "Choose where this part of the down payment comes from.",
      ),
    );
    if (source.source === "other") {
      issues.push(
        ...missingText(
          `down-payment-description-${source.id}`,
          `${capitalise(entry)} — description`,
          source.description,
          "Describe this down-payment source so it can be verified.",
        ),
      );
    }
    issues.push(
      ...missingText(
        `down-payment-amount-${source.id}`,
        `${capitalise(entry)} — amount`,
        source.amount,
        "Enter how much of the down payment comes from this source.",
      ),
      ...numberIssues(
        `down-payment-amount-${source.id}`,
        `${capitalise(entry)} — amount`,
        source.amount,
      ),
    );
  });
  return issues;
}

export function validateBorrowerDetails(
  prefix: string,
  borrowerLabel: string,
  value: BorrowerState,
  sinAlreadyProvided: boolean,
  coBorrower: boolean,
): FieldIssue[] {
  const issues: FieldIssue[] = [];
  const at = (label: string) => `${borrowerLabel} — ${label}`;

  const text: Array<[string, string, string, string]> = [
    [
      "first-name",
      "legal first name",
      value.first_name,
      "Enter your legal first name, as it appears on your ID.",
    ],
    [
      "last-name",
      "legal last name",
      value.last_name,
      "Enter your legal last name, as it appears on your ID.",
    ],
    [
      "email",
      "email",
      value.email,
      "Enter an email address we can use to reach you, for example name@example.com.",
    ],
    [
      "phone",
      "phone",
      value.phone,
      "Enter a 10-digit phone number, for example (519) 123-4567.",
    ],
    [
      "street",
      "street address",
      value.current_address.street,
      "Enter the street address where you currently live, for example 12 Main St.",
    ],
    [
      "city",
      "city",
      value.current_address.city,
      "Enter the city or town where you currently live.",
    ],
    [
      "postal",
      "postal code",
      value.current_address.postal_code,
      "Enter your postal code, for example N6H 4T6.",
    ],
  ];
  if (coBorrower) {
    text.push([
      "relationship",
      "relationship to the primary borrower",
      value.relationship_to_primary,
      "Describe how the co-borrower is related to the primary borrower, for example spouse.",
    ]);
  }
  for (const [field, label, candidate, message] of text) {
    issues.push(
      ...missingText(`${prefix}-${field}`, at(label), candidate, message),
    );
  }

  issues.push(
    ...missingChoice(
      `${prefix}-contact`,
      at("preferred contact method"),
      value.preferred_contact_method,
      "Choose how we should contact you — email or telephone.",
    ),
    ...missingChoice(
      `${prefix}-dob`,
      at("date of birth"),
      value.date_of_birth,
      "Enter the date of birth, for example 1985-04-23.",
    ),
    ...missingChoice(
      `${prefix}-marital`,
      at("marital status"),
      value.marital_status,
      "Choose a marital status from the list.",
    ),
    ...missingChoice(
      `${prefix}-province`,
      at("province or territory"),
      value.current_address.province,
      "Choose the province or territory where you currently live.",
    ),
  );

  if (!sinAlreadyProvided) {
    if (!/^\d{9}$/.test(value.sin)) {
      issues.push({
        field: `${prefix}-sin`,
        label: at("social insurance number"),
        message: "Enter all nine digits of the SIN, with no spaces.",
      });
    } else if (!passesSinChecksum(value.sin)) {
      issues.push({
        field: `${prefix}-sin`,
        label: at("social insurance number"),
        message:
          "That SIN fails its own check digit — re-read the nine digits on the card and correct them.",
      });
    }
  } else if (value.sin && !/^\d{9}$/.test(value.sin)) {
    issues.push({
      field: `${prefix}-sin`,
      label: at("replacement social insurance number"),
      message: "A replacement SIN must contain exactly nine digits.",
    });
  }

  if (value.email.trim() && !isValidEmail(value.email)) {
    issues.push({
      field: `${prefix}-email`,
      label: at("email"),
      message:
        "That email address is not complete — check it reads name@example.com.",
    });
  }
  if (value.phone.trim() && !isAcceptablePhoneInput(value.phone)) {
    issues.push({
      field: `${prefix}-phone`,
      label: at("phone"),
      message:
        "Enter a 10-digit phone number, for example (519) 123-4567. Add the + country code only for a number outside Canada or the US.",
    });
  }
  if (
    value.current_address.postal_code.trim() &&
    !isValidPostalCode(value.current_address.postal_code)
  ) {
    issues.push({
      field: `${prefix}-postal`,
      label: at("postal code"),
      message: "Enter a Canadian postal code, for example N6H 4T6.",
    });
  }

  issues.push(
    ...requiredNumber(
      `${prefix}-dependants`,
      at("number of dependants"),
      value.number_of_dependants,
      "Enter the number of dependants — enter 0 if there are none.",
    ),
    ...requiredNumber(
      `${prefix}-address-years`,
      at("years at address"),
      value.current_address.years_at_address,
      "Enter how many whole years you have lived at this address — enter 0 if it is under a year.",
    ),
    ...requiredNumber(
      `${prefix}-address-months`,
      at("months at address"),
      value.current_address.months_at_address,
      "Enter the extra months after those years (0 to 11) — enter 0 if none.",
    ),
  );
  return issues;
}

export function validateEmploymentEntries(
  prefix: string,
  borrowerLabel: string,
  entries: EmploymentState[],
): FieldIssue[] {
  return entries.flatMap((entry, index) => {
    const entryLabel = `${borrowerLabel} income entry ${index + 1}`;
    const removable = entries.length > 1;
    const removeHint = removable ? ", or remove this entry." : ".";
    const issues: FieldIssue[] = [
      ...missingChoice(
        `${prefix}-employment-type-${entry.id}`,
        `${entryLabel} — employment or income type`,
        entry.employment_type,
        "Choose the employment or income type for this entry.",
      ),
      ...missingText(
        `${prefix}-occupation-${entry.id}`,
        `${entryLabel} — occupation category`,
        entry.occupation_category,
        `Enter the occupation category, for example office administration${removeHint}`,
      ),
      ...missingText(
        `${prefix}-industry-${entry.id}`,
        `${entryLabel} — industry`,
        entry.industry,
        `Enter the industry, for example residential construction${removeHint}`,
      ),
      ...missingText(
        `${prefix}-income-${entry.id}`,
        `${entryLabel} — annual gross income`,
        entry.annual_gross_income,
        `Enter the annual gross income before deductions${removeHint}`,
      ),
      ...requiredNumber(
        `${prefix}-duration-years-${entry.id}`,
        `${entryLabel} — years in this role`,
        entry.duration_years,
        `Enter how many whole years you have been in this role — enter 0 if it is under a year${removeHint}`,
      ),
      ...requiredNumber(
        `${prefix}-duration-months-${entry.id}`,
        `${entryLabel} — months in this role`,
        entry.duration_months,
        `Enter the extra months after those years (0 to 11), or 0 if none.`,
      ),
      ...(entry.annual_gross_income.trim()
        ? numberIssues(
            `${prefix}-income-${entry.id}`,
            `${entryLabel} — annual gross income`,
            entry.annual_gross_income,
          )
        : []),
    ];
    return issues;
  });
}

export function validateAssetsAndLiabilities(
  assets: AssetState[],
  liabilities: LiabilityState[],
  assetsComplete: boolean,
  liabilitiesComplete: boolean,
): FieldIssue[] {
  return [
    ...assets.flatMap((asset, index) =>
      numberIssues(
        `asset-value-${asset.id}`,
        `Asset ${index + 1} value`,
        asset.value,
      ),
    ),
    ...liabilities.flatMap((liability, index) => [
      ...numberIssues(
        `liability-current_balance-${liability.id}`,
        `Liability ${index + 1} current balance`,
        liability.current_balance,
      ),
      ...numberIssues(
        `liability-payment_amount-${liability.id}`,
        `Liability ${index + 1} payment amount`,
        liability.payment_amount,
      ),
    ]),
    ...(assetsComplete
      ? []
      : [
          {
            field: "assets-complete",
            label: "Asset list completeness",
            message:
              "Tick this box to confirm the asset list is complete — including if you have none.",
          },
        ]),
    ...(liabilitiesComplete
      ? []
      : [
          {
            field: "liabilities-complete",
            label: "Liability list completeness",
            message:
              "Tick this box to confirm the liability list is complete — including if you have none.",
          },
        ]),
  ];
}

export function validateSubjectProperty(
  value: SubjectPropertyState,
): FieldIssue[] {
  if (!value.identified) return [];
  return [
    ...missingText(
      "subject-address",
      "Property address",
      value.address,
      "Enter the street address of the property.",
    ),
    ...missingText(
      "subject-city",
      "Property city",
      value.city,
      "Enter the city or town of the property.",
    ),
    ...missingChoice(
      "subject-province",
      "Property province",
      value.province,
      "Choose the province or territory of the property.",
    ),
    ...missingText(
      "subject-postal",
      "Property postal code",
      value.postal_code,
      "Enter the postal code of the property, for example N6H 4T6.",
    ),
    ...missingChoice(
      "subject-type",
      "Property type",
      value.property_type,
      "Choose the property type, for example single family or condo.",
    ),
    ...missingChoice(
      "subject-style",
      "Property style",
      value.property_style,
      "Choose the property style, for example detached or semi-detached.",
    ),
    ...missingChoice(
      "subject-occupancy",
      "Occupancy",
      value.occupancy,
      "Choose how the property will be occupied.",
    ),
    ...numberIssues(
      "subject-year_built",
      "Year built",
      value.year_built,
      "integer",
    ),
    ...numberIssues(
      "subject-livable_area_sqft",
      "Livable area",
      value.livable_area_sqft,
      "integer",
    ),
    ...numberIssues("subject-units", "Number of units", value.units, "integer"),
    ...numberIssues(
      "subject-monthly_property_tax",
      "Monthly property tax",
      value.monthly_property_tax,
    ),
    ...numberIssues(
      "subject-monthly_heating_cost",
      "Monthly heating cost",
      value.monthly_heating_cost,
    ),
    ...numberIssues(
      "subject-monthly_condo_fee",
      "Monthly condo fee",
      value.monthly_condo_fee,
    ),
  ];
}

export function validateOtherProperties(
  properties: OtherPropertyState[],
): FieldIssue[] {
  return properties.flatMap((property, index) => {
    const label = `Other property ${index + 1}`;
    return [
      ...numberIssues(
        `other-purchase_price-${property.id}`,
        `${label} purchase price`,
        property.purchase_price,
      ),
      ...numberIssues(
        `other-estimated_value-${property.id}`,
        `${label} estimated value`,
        property.estimated_value,
      ),
      ...property.mortgages.flatMap((mortgage, mortgageIndex) => [
        ...numberIssues(
          `other-mortgage-balance-${mortgage.id}`,
          `${label} mortgage ${mortgageIndex + 1} balance`,
          mortgage.balance,
        ),
        ...numberIssues(
          `other-mortgage-payment_amount-${mortgage.id}`,
          `${label} mortgage ${mortgageIndex + 1} payment amount`,
          mortgage.payment_amount,
        ),
      ]),
    ];
  });
}

/** Turn issues into the per-field messages the sections render. */
export function fieldMessages(issues: FieldIssue[]): Record<string, string> {
  const messages: Record<string, string> = {};
  for (const issue of issues) {
    if (!messages[issue.field]) messages[issue.field] = issue.message;
  }
  return messages;
}

/** Summary lines: what to fix, on which field, in which entry. */
export function issueLines(issues: FieldIssue[], limit = 4): string[] {
  return issues
    .slice(0, limit)
    .map((issue) => `${issue.label}: ${issue.message}`);
}

function capitalise(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
