import { Button, FormField } from "@keeper/ui";
import {
  emptyMortgage,
  emptyOtherProperty,
  type OtherPropertyState,
} from "./types";

export function OtherPropertiesSection({
  properties,
  onChange,
}: {
  properties: OtherPropertyState[];
  onChange: (value: OtherPropertyState[]) => void;
}) {
  const update = (
    propertyId: string,
    field: keyof OtherPropertyState,
    value: string | boolean,
  ) =>
    onChange(
      properties.map((property) =>
        property.id === propertyId ? { ...property, [field]: value } : property,
      ),
    );
  return (
    <fieldset>
      <legend>Other owned properties and mortgages</legend>
      <p>
        This optional group is for property you already own. Add no entry when
        it does not apply.
      </p>
      {properties.map((property, propertyIndex) => (
        <section className="repeat-entry" key={property.id}>
          <h3>Other property {propertyIndex + 1}</h3>
          <div className="borrower-form-grid">
            <FormField
              id={`other-address-${property.id}`}
              label="Property address"
            >
              <input
                id={`other-address-${property.id}`}
                value={property.address}
                onChange={(event) =>
                  update(property.id, "address", event.currentTarget.value)
                }
              />
            </FormField>
            {[
              ["purchase_date", "Purchase date"],
              ["purchase_price", "Purchase price"],
              ["estimated_value", "Estimated value"],
            ].map(([field, label]) => (
              <FormField
                id={`other-${field}-${property.id}`}
                label={label}
                key={field}
              >
                <input
                  id={`other-${field}-${property.id}`}
                  type={field === "purchase_date" ? "date" : "text"}
                  inputMode={field === "purchase_date" ? undefined : "decimal"}
                  value={
                    property[
                      field as
                        | "purchase_date"
                        | "purchase_price"
                        | "estimated_value"
                    ]
                  }
                  onChange={(event) =>
                    update(
                      property.id,
                      field as keyof OtherPropertyState,
                      event.currentTarget.value,
                    )
                  }
                />
              </FormField>
            ))}
          </div>
          <label className="consent">
            <input
              type="checkbox"
              checked={property.is_owner_occupied}
              onChange={(event) =>
                update(
                  property.id,
                  "is_owner_occupied",
                  event.currentTarget.checked,
                )
              }
            />
            <span>This property is owner-occupied.</span>
          </label>
          {property.mortgages.map((mortgage, mortgageIndex) => (
            <section className="repeat-entry nested-repeat" key={mortgage.id}>
              <h3>
                Property {propertyIndex + 1}, mortgage {mortgageIndex + 1}
              </h3>
              <div className="borrower-form-grid">
                {[
                  ["balance", "Balance (required)"],
                  ["payment_amount", "Payment amount (required)"],
                  ["payment_frequency", "Payment frequency (required)"],
                  ["maturity_date", "Maturity date (optional)"],
                ].map(([field, label]) => (
                  <FormField
                    id={`other-mortgage-${field}-${mortgage.id}`}
                    label={label}
                    key={field}
                  >
                    <input
                      id={`other-mortgage-${field}-${mortgage.id}`}
                      type={field === "maturity_date" ? "date" : "text"}
                      value={
                        mortgage[
                          field as
                            | "balance"
                            | "payment_amount"
                            | "payment_frequency"
                            | "maturity_date"
                        ]
                      }
                      onChange={(event) =>
                        onChange(
                          properties.map((item) =>
                            item.id === property.id
                              ? {
                                  ...item,
                                  mortgages: item.mortgages.map((candidate) =>
                                    candidate.id === mortgage.id
                                      ? {
                                          ...candidate,
                                          [field]: event.currentTarget.value,
                                        }
                                      : candidate,
                                  ),
                                }
                              : item,
                          ),
                        )
                      }
                    />
                  </FormField>
                ))}
              </div>
              <Button
                type="button"
                className="button-secondary"
                onClick={() =>
                  onChange(
                    properties.map((item) =>
                      item.id === property.id
                        ? {
                            ...item,
                            mortgages: item.mortgages.filter(
                              (candidate) => candidate.id !== mortgage.id,
                            ),
                          }
                        : item,
                    ),
                  )
                }
              >
                Remove mortgage {mortgageIndex + 1}
              </Button>
            </section>
          ))}
          <div className="button-row">
            <Button
              type="button"
              className="button-secondary"
              onClick={() =>
                onChange(
                  properties.map((item) =>
                    item.id === property.id
                      ? {
                          ...item,
                          mortgages: [...item.mortgages, emptyMortgage()],
                        }
                      : item,
                  ),
                )
              }
            >
              Add a mortgage to property {propertyIndex + 1}
            </Button>
            <Button
              type="button"
              className="button-secondary"
              onClick={() =>
                onChange(properties.filter((item) => item.id !== property.id))
              }
            >
              Remove other property {propertyIndex + 1}
            </Button>
          </div>
        </section>
      ))}
      {properties.length < 10 ? (
        <Button
          type="button"
          className="button-secondary"
          onClick={() => onChange([...properties, emptyOtherProperty()])}
        >
          Add another owned property
        </Button>
      ) : null}
    </fieldset>
  );
}
