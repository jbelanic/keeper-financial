/**
 * Turn a browser-safe validation issue into one sentence an applicant can act on.
 *
 * The API describes a rejected save with internal field paths and library
 * wording (`primary_borrower → current_address → postal_code:
 * "String should have at least 6 characters"`). Showing that verbatim tells the
 * applicant nothing and exposes the storage shape, so every message is mapped
 * here and the internal path is only used to place the message beside the field.
 */

/** One rejected field, as the API reports it in a 422 `detail` array. */
export type BorrowerIssue = {
  path: Array<string | number>;
  message: string;
};

const FIELD_LABELS: Record<string, string> = {
  payload: "Application",
  mortgage_request: "Mortgage request",
  mortgage_objective: "Mortgage purpose",
  requested_amount: "Requested mortgage amount",
  estimated_property_value: "Estimated property value",
  expected_closing_date: "Expected closing date",
  down_payment_sources: "Down-payment sources",
  preferred_agent_name: "Agent name",
  primary_borrower: "Primary borrower",
  co_borrower: "Co-borrower",
  first_name: "First name",
  last_name: "Last name",
  email: "Email",
  phone: "Phone number",
  preferred_contact_method: "Preferred contact method",
  date_of_birth: "Date of birth",
  sin: "Social insurance number",
  marital_status: "Marital status",
  number_of_dependants: "Number of dependants",
  relationship_to_primary: "Relationship to the primary borrower",
  current_address: "Current address",
  street: "Street address",
  city: "City",
  province: "Province or territory",
  postal_code: "Postal code",
  years_at_address: "Years at address",
  months_at_address: "Months at address",
  employment: "Employment entry",
  employment_type: "Employment or income type",
  employer_name: "Employer or business name",
  job_title: "Job title",
  occupation_category: "Occupation or category",
  industry: "Industry",
  duration_years: "Employment years",
  duration_months: "Employment months",
  annual_gross_income: "Annual gross income",
  employer_address: "Employer address",
  assets: "Asset",
  assets_complete: "Asset list confirmation",
  liabilities: "Liability",
  liabilities_complete: "Liability list confirmation",
  asset_type: "Asset type",
  value: "Asset value",
  liability_type: "Liability type",
  current_balance: "Current balance",
  payment_amount: "Payment amount",
  payment_frequency: "Payment frequency",
  description: "Description",
  subject_property: "Subject property",
  address: "Address",
  property_type: "Property type",
  property_style: "Property style",
  occupancy: "Occupancy",
  year_built: "Year built",
  livable_area_sqft: "Livable area in square feet",
  units: "Number of units",
  monthly_property_tax: "Monthly property tax",
  monthly_heating_cost: "Monthly heating cost",
  monthly_condo_fee: "Monthly condo fee",
  lot_details: "Lot details",
  garage_details: "Garage details",
  other_properties: "Other property",
  purchase_date: "Purchase date",
  purchase_price: "Purchase price",
  estimated_value: "Estimated value",
  mortgages: "Existing mortgage",
  balance: "Mortgage balance",
  maturity_date: "Maturity date",
  additional_notes: "Additional notes",
  source: "Source",
  amount: "Amount",
  // Public contact form
  name: "Name",
  telephone: "Telephone",
  message: "Message",
  service_contact_acknowledged: "Service-contact acknowledgement",
  marketing_consent: "Marketing consent",
  website: "Website",
  agent_reference: "Agent reference",
};

/** The human label for the deepest named field in an issue path. */
export function issueFieldLabel(path: Array<string | number>): string {
  for (let index = path.length - 1; index >= 0; index -= 1) {
    const part = path[index];
    if (typeof part === "string" && FIELD_LABELS[part])
      return FIELD_LABELS[part];
  }
  return "This answer";
}

const KNOWN_MESSAGES: Array<[RegExp, (match: RegExpMatchArray) => string]> = [
  [
    /^must be a valid email address$/,
    () => "Enter a valid email address, for example name@example.com.",
  ],
  [
    /^must be a valid North American phone number$/,
    () => "Enter a 10-digit phone number, for example (519) 123-4567.",
  ],
  [
    /^must be a valid Canadian postal code$/,
    () => "Enter a Canadian postal code, for example N6H 4T6.",
  ],
  [
    /^date of birth must be in the past$/,
    () => "Enter a date of birth that is in the past.",
  ],
  [
    /SIN failed Luhn validation/i,
    () => "That is not a valid SIN — check the nine digits you entered.",
  ],
  [
    /either requested_amount or estimated_property_value is required/i,
    () => "Enter a requested mortgage amount or an estimated property value.",
  ],
  [
    /^province must be a Canadian province or territory$/,
    () => "Choose a Canadian province or territory.",
  ],
  [
    /String should have at least (\d+) characters?/,
    (match) => `Enter at least ${match[1]} characters.`,
  ],
  [
    /String should have at most (\d+) characters?/,
    (match) => `Use at most ${match[1]} characters.`,
  ],
  [
    /Input should be a valid integer/,
    () => "Enter a whole number, for example 2.",
  ],
  [
    /Input should be a valid number/,
    () => "Enter a number, for example 650000.",
  ],
  [/Input should be greater than 0/, () => "Enter a number greater than zero."],
  [/Input should be greater than or equal to 0/, () => "Enter zero or more."],
  [
    /remove sensitive financial, identity, or authentication information/i,
    () =>
      "Remove sensitive financial, identity, or health details — the secure application is the place for those.",
  ],
  [/Field required/, () => "This is required."],
];

/**
 * One imperative sentence for a rejected answer.
 *
 * `message` has already had control characters stripped by the API client, so
 * this only ever sees plain text; an unrecognised message becomes a generic
 * sentence rather than the library's wording.
 */
export function humaniseIssueMessage(message: string): string {
  const cleaned = message.replace(/^Value error,\s*/i, "").trim();
  for (const [pattern, render] of KNOWN_MESSAGES) {
    const match = cleaned.match(pattern);
    if (match) return render(match);
  }
  if (/must be a valid/i.test(cleaned)) {
    return "Check this answer — the value is not in the expected format.";
  }
  return "Check this answer — it was not accepted.";
}

/** The summary line for an issue: "Postal code: Enter a Canadian postal code…" */
export function issueSummary(issue: BorrowerIssue): string {
  return `${issueFieldLabel(issue.path)}: ${humaniseIssueMessage(issue.message)}`;
}

/**
 * Read a FastAPI/pydantic `detail` array into issues.
 *
 * Used by surfaces that talk to the API directly (the public contact form) so
 * they can mark the field instead of showing one generic sentence. Anything that
 * is not a `{loc, msg}` entry is ignored rather than rendered.
 */
export function parseIssueDetail(detail: unknown): BorrowerIssue[] {
  if (!Array.isArray(detail)) return [];
  return detail.flatMap((item): BorrowerIssue[] => {
    if (!item || typeof item !== "object") return [];
    const issue = item as { loc?: unknown; msg?: unknown };
    if (typeof issue.msg !== "string") return [];
    const message = issue.msg
      .replace(/[\u0000-\u001f\u007f]/g, " ")
      .slice(0, 200);
    const path = Array.isArray(issue.loc)
      ? issue.loc.filter(
          (part): part is string | number =>
            typeof part === "string" || typeof part === "number",
        )
      : [];
    return message ? [{ path, message }] : [];
  });
}
