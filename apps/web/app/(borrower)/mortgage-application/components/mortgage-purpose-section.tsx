import { FormField } from "@keeper/ui";
import { Button } from "@keeper/ui";
import { emptyDownPayment, type MortgageRequestState } from "./types";

export function MortgagePurposeSection({
  value,
  onChange,
}: {
  value: MortgageRequestState;
  onChange: (value: MortgageRequestState) => void;
}) {
  const set = (field: keyof MortgageRequestState, next: string) =>
    onChange({ ...value, [field]: next });
  return (
    <fieldset>
      <legend>Mortgage request</legend>
      <p>
        Tell us what you are planning. Amounts are estimates and do not
        represent an approval or commitment.
      </p>
      <div className="borrower-form-grid">
        <FormField id="mortgage-objective" label="Mortgage purpose (required)">
          <select
            id="mortgage-objective"
            value={value.mortgage_objective}
            onChange={(event) =>
              set("mortgage_objective", event.currentTarget.value)
            }
          >
            <option value="">Select a purpose</option>
            <option value="purchase">Purchase</option>
            <option value="refinance">Refinance</option>
            <option value="renewal">Renewal or switch</option>
            <option value="pre_approval">Pre-approval</option>
          </select>
        </FormField>
        <FormField
          id="requested-amount"
          label="Requested mortgage amount"
          hint="Required when it is the applicable estimate."
        >
          <input
            id="requested-amount"
            inputMode="decimal"
            value={value.requested_amount}
            onChange={(event) =>
              set("requested_amount", event.currentTarget.value)
            }
          />
        </FormField>
        <FormField
          id="estimated-property-value"
          label="Estimated property value"
          hint="Required when it is the applicable estimate."
        >
          <input
            id="estimated-property-value"
            inputMode="decimal"
            value={value.estimated_property_value}
            onChange={(event) =>
              set("estimated_property_value", event.currentTarget.value)
            }
          />
        </FormField>
        <FormField
          id="expected-closing-date"
          label="Expected closing date (optional)"
        >
          <input
            id="expected-closing-date"
            type="date"
            value={value.expected_closing_date}
            onChange={(event) =>
              set("expected_closing_date", event.currentTarget.value)
            }
          />
        </FormField>
      </div>
      <h3>Down-payment sources</h3>
      <p>Add each source when it applies to this request.</p>
      {value.down_payment_sources.map((entry, index) => (
        <section className="repeat-entry" key={entry.id}>
          <h3>Down-payment source {index + 1}</h3>
          <div className="borrower-form-grid">
            <FormField
              id={`down-payment-source-${entry.id}`}
              label="Source (required)"
            >
              <select
                id={`down-payment-source-${entry.id}`}
                value={entry.source}
                onChange={(event) =>
                  onChange({
                    ...value,
                    down_payment_sources: value.down_payment_sources.map(
                      (candidate) =>
                        candidate.id === entry.id
                          ? {
                              ...candidate,
                              source: event.currentTarget.value,
                            }
                          : candidate,
                    ),
                  })
                }
              >
                <option value="">Select a source</option>
                <option value="savings">Savings</option>
                <option value="gift">Gift</option>
                <option value="home_equity">Home equity</option>
                <option value="other">Other</option>
              </select>
            </FormField>
            <FormField
              id={`down-payment-amount-${entry.id}`}
              label="Amount (required)"
            >
              <input
                id={`down-payment-amount-${entry.id}`}
                inputMode="decimal"
                value={entry.amount}
                onChange={(event) =>
                  onChange({
                    ...value,
                    down_payment_sources: value.down_payment_sources.map(
                      (candidate) =>
                        candidate.id === entry.id
                          ? { ...candidate, amount: event.currentTarget.value }
                          : candidate,
                    ),
                  })
                }
              />
            </FormField>
            <FormField
              id={`down-payment-description-${entry.id}`}
              label="Description (required for Other)"
            >
              <input
                id={`down-payment-description-${entry.id}`}
                maxLength={500}
                value={entry.description}
                onChange={(event) =>
                  onChange({
                    ...value,
                    down_payment_sources: value.down_payment_sources.map(
                      (candidate) =>
                        candidate.id === entry.id
                          ? {
                              ...candidate,
                              description: event.currentTarget.value,
                            }
                          : candidate,
                    ),
                  })
                }
              />
            </FormField>
          </div>
          <Button
            type="button"
            className="button-secondary"
            onClick={() =>
              onChange({
                ...value,
                down_payment_sources: value.down_payment_sources.filter(
                  (candidate) => candidate.id !== entry.id,
                ),
              })
            }
          >
            Remove down-payment source {index + 1}
          </Button>
        </section>
      ))}
      {value.down_payment_sources.length < 10 ? (
        <Button
          type="button"
          className="button-secondary"
          onClick={() =>
            onChange({
              ...value,
              down_payment_sources: [
                ...value.down_payment_sources,
                emptyDownPayment(),
              ],
            })
          }
        >
          Add a down-payment source
        </Button>
      ) : null}
    </fieldset>
  );
}
