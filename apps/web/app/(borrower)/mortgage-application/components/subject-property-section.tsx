import { FormField } from "@keeper/ui";
import type { SubjectPropertyState } from "./types";

export function SubjectPropertySection({
  value,
  onChange,
}: {
  value: SubjectPropertyState;
  onChange: (value: SubjectPropertyState) => void;
}) {
  const set = (field: keyof SubjectPropertyState, next: string | boolean) =>
    onChange({ ...value, [field]: next });
  return (
    <fieldset>
      <legend>Subject property</legend>
      <p>
        Property details are optional for a pre-approval and required when you
        have identified a property.
      </p>
      <label className="consent">
        <input
          type="checkbox"
          checked={value.identified}
          onChange={(event) => set("identified", event.currentTarget.checked)}
        />
        <span>I have identified the property for this request.</span>
      </label>
      {value.identified ? (
        <div className="borrower-form-grid">
          <FormField id="subject-address" label="Address (required)">
            <input
              id="subject-address"
              value={value.address}
              onChange={(event) => set("address", event.currentTarget.value)}
            />
          </FormField>
          <FormField id="subject-city" label="City (required)">
            <input
              id="subject-city"
              value={value.city}
              onChange={(event) => set("city", event.currentTarget.value)}
            />
          </FormField>
          <FormField
            id="subject-province"
            label="Province or territory (required)"
          >
            <input
              id="subject-province"
              maxLength={2}
              value={value.province}
              onChange={(event) => set("province", event.currentTarget.value)}
            />
          </FormField>
          <FormField id="subject-postal" label="Postal code (required)">
            <input
              id="subject-postal"
              maxLength={7}
              value={value.postal_code}
              onChange={(event) =>
                set("postal_code", event.currentTarget.value)
              }
            />
          </FormField>
          <FormField id="subject-type" label="Property type (required)">
            <select
              id="subject-type"
              value={value.property_type}
              onChange={(event) =>
                set("property_type", event.currentTarget.value)
              }
            >
              <option value="">Select a type</option>
              <option value="single_family">Single family</option>
              <option value="condo">Condo</option>
              <option value="townhouse">Townhouse</option>
              <option value="multi_family">Multi-family</option>
              <option value="manufactured">Manufactured</option>
              <option value="other">Other</option>
            </select>
          </FormField>
          <FormField id="subject-style" label="Property style (required)">
            <input
              id="subject-style"
              maxLength={100}
              value={value.property_style}
              onChange={(event) =>
                set("property_style", event.currentTarget.value)
              }
            />
          </FormField>
          <FormField id="subject-occupancy" label="Occupancy (required)">
            <select
              id="subject-occupancy"
              value={value.occupancy}
              onChange={(event) => set("occupancy", event.currentTarget.value)}
            >
              <option value="">Select occupancy</option>
              <option value="owner_occupied">Owner occupied</option>
              <option value="rental">Rental</option>
              <option value="second_home">Second home</option>
              <option value="other">Other</option>
            </select>
          </FormField>
          {[
            ["year_built", "Year built (optional)"],
            ["livable_area_sqft", "Livable area in sq. ft. (optional)"],
            ["units", "Number of units (optional)"],
            ["monthly_property_tax", "Monthly property tax (optional)"],
            ["monthly_heating_cost", "Monthly heating cost (optional)"],
            ["monthly_condo_fee", "Monthly condo fee (optional)"],
          ].map(([field, label]) => (
            <FormField id={`subject-${field}`} label={label} key={field}>
              <input
                id={`subject-${field}`}
                inputMode="decimal"
                value={
                  value[
                    field as
                      | "year_built"
                      | "livable_area_sqft"
                      | "units"
                      | "monthly_property_tax"
                      | "monthly_heating_cost"
                      | "monthly_condo_fee"
                  ]
                }
                onChange={(event) =>
                  set(
                    field as keyof SubjectPropertyState,
                    event.currentTarget.value,
                  )
                }
              />
            </FormField>
          ))}
          <FormField id="subject-lot-details" label="Lot details (optional)">
            <input
              id="subject-lot-details"
              maxLength={200}
              value={value.lot_details}
              onChange={(event) =>
                set("lot_details", event.currentTarget.value)
              }
            />
          </FormField>
          <FormField
            id="subject-garage-details"
            label="Garage details (optional)"
          >
            <input
              id="subject-garage-details"
              maxLength={200}
              value={value.garage_details}
              onChange={(event) =>
                set("garage_details", event.currentTarget.value)
              }
            />
          </FormField>
        </div>
      ) : (
        <p>
          No subject-property details will be included in this draft section.
        </p>
      )}
    </fieldset>
  );
}
