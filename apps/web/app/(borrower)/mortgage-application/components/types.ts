export type MortgageRequestState = {
  mortgage_objective: string;
  requested_amount: string;
  estimated_property_value: string;
  expected_closing_date: string;
  preferred_agent_slug: string;
  down_payment_sources: DownPaymentState[];
};

export type DownPaymentState = {
  id: string;
  source: string;
  amount: string;
  description: string;
};

export type AddressState = {
  street: string;
  city: string;
  province: string;
  postal_code: string;
  years_at_address: string;
  months_at_address: string;
};

export type BorrowerState = {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  preferred_contact_method: string;
  date_of_birth: string;
  sin: string;
  marital_status: string;
  number_of_dependants: string;
  relationship_to_primary: string;
  current_address: AddressState;
};

export type EmploymentState = {
  id: string;
  employment_type: string;
  employer_name: string;
  job_title: string;
  occupation_category: string;
  industry: string;
  duration_years: string;
  duration_months: string;
  annual_gross_income: string;
  employer_address: string;
};

export type AssetState = {
  id: string;
  asset_type: string;
  value: string;
  description: string;
};

export type LiabilityState = {
  id: string;
  liability_type: string;
  current_balance: string;
  payment_amount: string;
  payment_frequency: string;
  description: string;
};

export type SubjectPropertyStyle =
  | ""
  | "detached"
  | "semi_detached"
  | "townhouse_row"
  | "apartment"
  | "other";

export type SubjectPropertyOccupancy =
  | ""
  | "owner_occupied"
  | "tenant"
  | "vacant"
  | "other";

export type SubjectPropertyState = {
  identified: boolean;
  address: string;
  city: string;
  province: string;
  postal_code: string;
  property_type: string;
  property_style: SubjectPropertyStyle;
  occupancy: SubjectPropertyOccupancy;
  year_built: string;
  livable_area_sqft: string;
  units: string;
  monthly_property_tax: string;
  monthly_heating_cost: string;
  monthly_condo_fee: string;
  lot_details: string;
  garage_details: string;
};

export type MortgageState = {
  id: string;
  balance: string;
  payment_amount: string;
  payment_frequency: string;
  maturity_date: string;
};

export type OtherPropertyState = {
  id: string;
  address: string;
  purchase_date: string;
  purchase_price: string;
  estimated_value: string;
  is_owner_occupied: boolean;
  mortgages: MortgageState[];
};

let repeatId = 0;
export function nextRepeatId(prefix: string) {
  repeatId += 1;
  return `${prefix}-${repeatId}`;
}

export const emptyAddress = (): AddressState => ({
  street: "",
  city: "",
  province: "",
  postal_code: "",
  years_at_address: "0",
  months_at_address: "0",
});

export const emptyBorrower = (): BorrowerState => ({
  first_name: "",
  last_name: "",
  email: "",
  phone: "",
  preferred_contact_method: "",
  date_of_birth: "",
  sin: "",
  marital_status: "",
  number_of_dependants: "0",
  relationship_to_primary: "",
  current_address: emptyAddress(),
});

export const emptyEmployment = (): EmploymentState => ({
  id: nextRepeatId("employment"),
  employment_type: "",
  employer_name: "",
  job_title: "",
  occupation_category: "",
  industry: "",
  duration_years: "0",
  duration_months: "0",
  annual_gross_income: "",
  employer_address: "",
});

export const emptyAsset = (): AssetState => ({
  id: nextRepeatId("asset"),
  asset_type: "",
  value: "",
  description: "",
});

export const emptyDownPayment = (): DownPaymentState => ({
  id: nextRepeatId("down-payment"),
  source: "",
  amount: "",
  description: "",
});

export const emptyLiability = (): LiabilityState => ({
  id: nextRepeatId("liability"),
  liability_type: "",
  current_balance: "",
  payment_amount: "",
  payment_frequency: "",
  description: "",
});

export const emptyMortgage = (): MortgageState => ({
  id: nextRepeatId("mortgage"),
  balance: "",
  payment_amount: "",
  payment_frequency: "",
  maturity_date: "",
});

export const emptyOtherProperty = (): OtherPropertyState => ({
  id: nextRepeatId("property"),
  address: "",
  purchase_date: "",
  purchase_price: "",
  estimated_value: "",
  is_owner_occupied: false,
  mortgages: [],
});
