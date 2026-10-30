import { Button, FormField } from "@keeper/ui";
import { PHONE_EXAMPLE } from "@/lib/phone";
import type { BorrowerState } from "./types";

const provinces = [
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
];

function BorrowerFields({
  prefix,
  label,
  value,
  sinProvided,
  coBorrower,
  fieldErrors,
  onChange,
}: {
  prefix: string;
  label: string;
  value: BorrowerState;
  sinProvided: boolean;
  coBorrower?: boolean;
  fieldErrors?: Record<string, string>;
  onChange: (value: BorrowerState) => void;
}) {
  const set = (field: keyof BorrowerState, next: string) =>
    onChange({ ...value, [field]: next });
  const setAddress = (
    field: keyof BorrowerState["current_address"],
    next: string,
  ) =>
    onChange({
      ...value,
      current_address: { ...value.current_address, [field]: next },
    });
  return (
    <fieldset>
      <legend>{label}</legend>
      <div className="borrower-form-grid">
        <FormField
          id={`${prefix}-first-name`}
          label="Legal first name (required)"
          error={fieldErrors?.[`${prefix}-first-name`]}
        >
          <input
            id={`${prefix}-first-name`}
            autoComplete="given-name"
            value={value.first_name}
            onChange={(event) => set("first_name", event.currentTarget.value)}
          />
        </FormField>
        <FormField
          id={`${prefix}-last-name`}
          label="Legal last name (required)"
          error={fieldErrors?.[`${prefix}-last-name`]}
        >
          <input
            id={`${prefix}-last-name`}
            autoComplete="family-name"
            value={value.last_name}
            onChange={(event) => set("last_name", event.currentTarget.value)}
          />
        </FormField>
        <FormField
          id={`${prefix}-email`}
          label="Email (required)"
          error={fieldErrors?.[`${prefix}-email`]}
        >
          <input
            id={`${prefix}-email`}
            type="email"
            autoComplete="email"
            value={value.email}
            onChange={(event) => set("email", event.currentTarget.value)}
          />
        </FormField>
        <FormField
          id={`${prefix}-phone`}
          label="Phone (required)"
          hint={`10 digits is enough — for example ${PHONE_EXAMPLE}.`}
          error={fieldErrors?.[`${prefix}-phone`]}
        >
          <input
            id={`${prefix}-phone`}
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder={PHONE_EXAMPLE}
            value={value.phone}
            onChange={(event) => set("phone", event.currentTarget.value)}
          />
        </FormField>
        <FormField
          id={`${prefix}-contact`}
          label="Preferred contact method (required)"
          error={fieldErrors?.[`${prefix}-contact`]}
        >
          <select
            id={`${prefix}-contact`}
            value={value.preferred_contact_method}
            onChange={(event) =>
              set("preferred_contact_method", event.currentTarget.value)
            }
          >
            <option value="">Select a method</option>
            <option value="email">Email</option>
            <option value="phone">Phone</option>
          </select>
        </FormField>
        <FormField
          id={`${prefix}-dob`}
          label="Date of birth (required)"
          error={fieldErrors?.[`${prefix}-dob`]}
        >
          <input
            id={`${prefix}-dob`}
            type="date"
            autoComplete="bday"
            value={value.date_of_birth}
            onChange={(event) =>
              set("date_of_birth", event.currentTarget.value)
            }
          />
        </FormField>
        <FormField
          id={`${prefix}-sin`}
          label={`Social Insurance Number (${sinProvided ? "replace only" : "required"})`}
          hint={
            sinProvided
              ? "SIN provided ••• ••• •••. Enter all nine digits only to replace it; the saved value cannot be retrieved."
              : "Enter nine digits. It is encrypted and will not be shown again."
          }
          error={fieldErrors?.[`${prefix}-sin`]}
        >
          <input
            id={`${prefix}-sin`}
            inputMode="numeric"
            autoComplete="off"
            maxLength={9}
            value={value.sin}
            onChange={(event) =>
              set(
                "sin",
                event.currentTarget.value.replace(/\D/g, "").slice(0, 9),
              )
            }
          />
        </FormField>
        <FormField
          id={`${prefix}-marital`}
          label="Marital status (required)"
          error={fieldErrors?.[`${prefix}-marital`]}
        >
          <select
            id={`${prefix}-marital`}
            value={value.marital_status}
            onChange={(event) =>
              set("marital_status", event.currentTarget.value)
            }
          >
            <option value="">Select a status</option>
            <option value="single">Single</option>
            <option value="married">Married</option>
            <option value="common_law">Common law</option>
            <option value="separated">Separated</option>
            <option value="divorced">Divorced</option>
            <option value="widowed">Widowed</option>
          </select>
        </FormField>
        <FormField
          id={`${prefix}-dependants`}
          label="Number of dependants (required)"
          error={fieldErrors?.[`${prefix}-dependants`]}
        >
          <input
            id={`${prefix}-dependants`}
            type="number"
            min="0"
            max="20"
            value={value.number_of_dependants}
            onChange={(event) =>
              set("number_of_dependants", event.currentTarget.value)
            }
          />
        </FormField>
        {coBorrower ? (
          <FormField
            id={`${prefix}-relationship`}
            label="Relationship to primary borrower (required)"
            error={fieldErrors?.[`${prefix}-relationship`]}
          >
            <input
              id={`${prefix}-relationship`}
              maxLength={100}
              value={value.relationship_to_primary}
              onChange={(event) =>
                set("relationship_to_primary", event.currentTarget.value)
              }
            />
          </FormField>
        ) : null}
      </div>
      <h3>Current address</h3>
      <div className="borrower-form-grid">
        <FormField
          id={`${prefix}-street`}
          label="Street address (required)"
          error={fieldErrors?.[`${prefix}-street`]}
        >
          <input
            id={`${prefix}-street`}
            autoComplete="street-address"
            value={value.current_address.street}
            onChange={(event) =>
              setAddress("street", event.currentTarget.value)
            }
          />
        </FormField>
        <FormField
          id={`${prefix}-city`}
          label="City (required)"
          error={fieldErrors?.[`${prefix}-city`]}
        >
          <input
            id={`${prefix}-city`}
            autoComplete="address-level2"
            value={value.current_address.city}
            onChange={(event) => setAddress("city", event.currentTarget.value)}
          />
        </FormField>
        <FormField
          id={`${prefix}-province`}
          label="Province or territory (required)"
          error={fieldErrors?.[`${prefix}-province`]}
        >
          <select
            id={`${prefix}-province`}
            autoComplete="address-level1"
            value={value.current_address.province}
            onChange={(event) =>
              setAddress("province", event.currentTarget.value)
            }
          >
            <option value="">Select</option>
            {provinces.map((province) => (
              <option key={province}>{province}</option>
            ))}
          </select>
        </FormField>
        <FormField
          id={`${prefix}-postal`}
          label="Postal code (required)"
          error={fieldErrors?.[`${prefix}-postal`]}
        >
          <input
            id={`${prefix}-postal`}
            autoComplete="postal-code"
            value={value.current_address.postal_code}
            onChange={(event) =>
              setAddress("postal_code", event.currentTarget.value)
            }
          />
        </FormField>
        <FormField
          id={`${prefix}-address-years`}
          label="Years at address (required)"
          error={fieldErrors?.[`${prefix}-address-years`]}
        >
          <input
            id={`${prefix}-address-years`}
            type="number"
            min="0"
            max="100"
            value={value.current_address.years_at_address}
            onChange={(event) =>
              setAddress("years_at_address", event.currentTarget.value)
            }
          />
        </FormField>
        <FormField
          id={`${prefix}-address-months`}
          label="Additional months (required)"
          error={fieldErrors?.[`${prefix}-address-months`]}
        >
          <input
            id={`${prefix}-address-months`}
            type="number"
            min="0"
            max="11"
            value={value.current_address.months_at_address}
            onChange={(event) =>
              setAddress("months_at_address", event.currentTarget.value)
            }
          />
        </FormField>
      </div>
    </fieldset>
  );
}

export function BorrowerDetailsSection({
  primary,
  coBorrower,
  hasSavedPrimarySin,
  hasSavedCoBorrower,
  fieldErrors,
  onPrimaryChange,
  onCoBorrowerChange,
  onAddCoBorrower,
  onRemoveCoBorrower,
}: {
  primary: BorrowerState;
  coBorrower: BorrowerState | null;
  hasSavedPrimarySin: boolean;
  hasSavedCoBorrower: boolean;
  fieldErrors?: Record<string, string>;
  onPrimaryChange: (value: BorrowerState) => void;
  onCoBorrowerChange: (value: BorrowerState) => void;
  onAddCoBorrower: () => void;
  onRemoveCoBorrower: () => void;
}) {
  return (
    <>
      <BorrowerFields
        fieldErrors={fieldErrors}
        prefix="primary"
        label="Primary borrower"
        value={primary}
        sinProvided={hasSavedPrimarySin}
        onChange={onPrimaryChange}
      />
      {coBorrower ? (
        <>
          <BorrowerFields
            fieldErrors={fieldErrors}
            prefix="co"
            label="Co-borrower"
            value={coBorrower}
            sinProvided={hasSavedCoBorrower}
            coBorrower
            onChange={onCoBorrowerChange}
          />
          <Button
            type="button"
            className="button-secondary"
            onClick={onRemoveCoBorrower}
          >
            Remove co-borrower
          </Button>
        </>
      ) : (
        <Button
          type="button"
          className="button-secondary"
          onClick={onAddCoBorrower}
        >
          Add a co-borrower
        </Button>
      )}
    </>
  );
}
