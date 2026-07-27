import {
  emptyBorrower,
  emptyEmployment,
  type AssetState,
  type BorrowerState,
  type DownPaymentState,
  type EmploymentState,
  type LiabilityState,
  type MortgageRequestState,
  type OtherPropertyState,
  type SubjectPropertyOccupancy,
  type SubjectPropertyState,
  type SubjectPropertyStyle,
} from "./components/types";

export type HydratedBorrowerDraft = {
  mortgage: MortgageRequestState;
  primary: BorrowerState;
  coBorrower: BorrowerState | null;
  primaryEmployment: EmploymentState[];
  coEmployment: EmploymentState[] | null;
  assets: AssetState[];
  liabilities: LiabilityState[];
  assetsComplete: boolean;
  liabilitiesComplete: boolean;
  subjectProperty: SubjectPropertyState;
  otherProperties: OtherPropertyState[];
  notes: string;
  resumeStep: number;
};

const record = (value: unknown): Record<string, unknown> =>
  value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
const items = (value: unknown): unknown[] =>
  Array.isArray(value) ? value : [];
const text = (value: unknown): string =>
  typeof value === "string" || typeof value === "number" ? String(value) : "";
const flag = (value: unknown): boolean => value === true;
const has = (value: Record<string, unknown>, key: string): boolean =>
  Object.prototype.hasOwnProperty.call(value, key);

function borrower(value: unknown): BorrowerState {
  const source = record(value);
  const address = record(source.current_address);
  return {
    ...emptyBorrower(),
    first_name: text(source.first_name),
    last_name: text(source.last_name),
    email: text(source.email),
    phone: text(source.phone),
    preferred_contact_method: text(source.preferred_contact_method),
    date_of_birth: text(source.date_of_birth),
    sin: "",
    marital_status: text(source.marital_status),
    number_of_dependants: text(source.number_of_dependants) || "0",
    relationship_to_primary: text(source.relationship_to_primary),
    current_address: {
      street: text(address.street),
      city: text(address.city),
      province: text(address.province),
      postal_code: text(address.postal_code),
      years_at_address: text(address.years_at_address) || "0",
      months_at_address: text(address.months_at_address) || "0",
    },
  };
}

function employment(value: unknown): EmploymentState[] {
  const restored = items(value).map((entry, index) => {
    const source = record(entry);
    return {
      id: `recovered-employment-${index}`,
      employment_type: text(source.employment_type),
      employer_name: text(source.employer_name),
      job_title: text(source.job_title),
      occupation_category: text(source.occupation_category),
      industry: text(source.industry),
      duration_years: text(source.duration_years) || "0",
      duration_months: text(source.duration_months) || "0",
      annual_gross_income: text(source.annual_gross_income),
      employer_address: text(source.employer_address),
    };
  });
  return restored.length ? restored : [emptyEmployment()];
}

function downPayments(value: unknown): DownPaymentState[] {
  return items(value).map((entry, index) => {
    const source = record(entry);
    return {
      id: `recovered-down-payment-${index}`,
      source: text(source.source),
      amount: text(source.amount),
      description: text(source.description),
    };
  });
}

function subjectProperty(value: unknown): SubjectPropertyState {
  const source = record(value);
  const styles = new Set<SubjectPropertyStyle>([
    "detached",
    "semi_detached",
    "townhouse_row",
    "apartment",
    "other",
  ]);
  const occupancies = new Set<SubjectPropertyOccupancy>([
    "owner_occupied",
    "tenant",
    "vacant",
    "other",
  ]);
  const style = text(source.property_style) as SubjectPropertyStyle;
  const occupancy = text(source.occupancy) as SubjectPropertyOccupancy;
  return {
    identified: value !== null && value !== undefined,
    address: text(source.address),
    city: text(source.city),
    province: text(source.province),
    postal_code: text(source.postal_code),
    property_type: text(source.property_type),
    property_style: styles.has(style) ? style : "",
    occupancy: occupancies.has(occupancy) ? occupancy : "",
    year_built: text(source.year_built),
    livable_area_sqft: text(source.livable_area_sqft),
    units: text(source.units),
    monthly_property_tax: text(source.monthly_property_tax),
    monthly_heating_cost: text(source.monthly_heating_cost),
    monthly_condo_fee: text(source.monthly_condo_fee),
    lot_details: text(source.lot_details),
    garage_details: text(source.garage_details),
  };
}

function otherProperties(value: unknown): OtherPropertyState[] {
  return items(value).map((entry, propertyIndex) => {
    const source = record(entry);
    return {
      id: `recovered-property-${propertyIndex}`,
      address: text(source.address),
      purchase_date: text(source.purchase_date),
      purchase_price: text(source.purchase_price),
      estimated_value: text(source.estimated_value),
      is_owner_occupied: flag(source.is_owner_occupied),
      mortgages: items(source.mortgages).map((mortgage, mortgageIndex) => {
        const restored = record(mortgage);
        return {
          id: `recovered-property-${propertyIndex}-mortgage-${mortgageIndex}`,
          balance: text(restored.balance),
          payment_amount: text(restored.payment_amount),
          payment_frequency: text(restored.payment_frequency),
          maturity_date: text(restored.maturity_date),
        };
      }),
    };
  });
}

export function hydrateBorrowerDraft(
  payload: Record<string, unknown>,
  preferredAgentSlug = "",
): HydratedBorrowerDraft {
  const mortgageRequest = record(payload.mortgage_request);
  const primarySource = record(payload.primary_borrower);
  const coSource = record(payload.co_borrower);
  const hasCoBorrower =
    payload.co_borrower !== null && has(payload, "co_borrower");
  const assets = items(payload.assets).map((entry, index) => {
    const source = record(entry);
    return {
      id: `recovered-asset-${index}`,
      asset_type: text(source.asset_type),
      value: text(source.value),
      description: text(source.description),
    };
  });
  const liabilities = items(payload.liabilities).map((entry, index) => {
    const source = record(entry);
    return {
      id: `recovered-liability-${index}`,
      liability_type: text(source.liability_type),
      current_balance: text(source.current_balance),
      payment_amount: text(source.payment_amount),
      payment_frequency: text(source.payment_frequency),
      description: text(source.description),
    };
  });

  let resumeStep = 0;
  if (has(payload, "mortgage_request")) resumeStep = 1;
  if (has(payload, "primary_borrower")) resumeStep = 2;
  if (has(primarySource, "employment")) resumeStep = 3;
  if (has(payload, "assets_complete") || has(payload, "liabilities_complete")) {
    resumeStep = 4;
  }
  if (has(payload, "subject_property")) resumeStep = 5;
  if (has(payload, "other_properties")) resumeStep = 6;
  if (has(payload, "additional_notes")) resumeStep = 7;

  return {
    mortgage: {
      mortgage_objective: text(mortgageRequest.mortgage_objective),
      requested_amount: text(mortgageRequest.requested_amount),
      estimated_property_value: text(mortgageRequest.estimated_property_value),
      expected_closing_date: text(mortgageRequest.expected_closing_date),
      preferred_agent_slug:
        text(mortgageRequest.preferred_agent_slug) || preferredAgentSlug,
      down_payment_sources: downPayments(mortgageRequest.down_payment_sources),
    },
    primary: borrower(primarySource),
    coBorrower: hasCoBorrower ? borrower(coSource) : null,
    primaryEmployment: employment(primarySource.employment),
    coEmployment: hasCoBorrower ? employment(coSource.employment) : null,
    assets,
    liabilities,
    assetsComplete: flag(payload.assets_complete),
    liabilitiesComplete: flag(payload.liabilities_complete),
    subjectProperty: subjectProperty(payload.subject_property),
    otherProperties: otherProperties(payload.other_properties),
    notes: text(payload.additional_notes),
    resumeStep,
  };
}
