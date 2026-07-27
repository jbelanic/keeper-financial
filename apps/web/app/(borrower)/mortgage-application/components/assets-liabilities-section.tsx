import { Button, FormField } from "@keeper/ui";
import {
  emptyAsset,
  emptyLiability,
  type AssetState,
  type LiabilityState,
} from "./types";

export function AssetsLiabilitiesSection({
  assets,
  liabilities,
  assetsComplete,
  liabilitiesComplete,
  onAssetsChange,
  onLiabilitiesChange,
  onAssetsCompleteChange,
  onLiabilitiesCompleteChange,
}: {
  assets: AssetState[];
  liabilities: LiabilityState[];
  assetsComplete: boolean;
  liabilitiesComplete: boolean;
  onAssetsChange: (entries: AssetState[]) => void;
  onLiabilitiesChange: (entries: LiabilityState[]) => void;
  onAssetsCompleteChange: (value: boolean) => void;
  onLiabilitiesCompleteChange: (value: boolean) => void;
}) {
  return (
    <>
      <fieldset>
        <legend>Assets</legend>
        <p>Add assets that apply. Descriptions are required for “Other.”</p>
        {assets.map((entry, index) => (
          <section className="repeat-entry" key={entry.id}>
            <h3>Asset {index + 1}</h3>
            <div className="borrower-form-grid">
              <FormField
                id={`asset-type-${entry.id}`}
                label="Asset type (required)"
              >
                <select
                  id={`asset-type-${entry.id}`}
                  value={entry.asset_type}
                  onChange={(event) =>
                    onAssetsChange(
                      assets.map((item) =>
                        item.id === entry.id
                          ? { ...item, asset_type: event.currentTarget.value }
                          : item,
                      ),
                    )
                  }
                >
                  <option value="">Select a type</option>
                  {[
                    "savings",
                    "chequing",
                    "investment",
                    "rrsp",
                    "tfsa",
                    "pension",
                    "real_estate",
                    "vehicle",
                    "other",
                  ].map((option) => (
                    <option value={option} key={option}>
                      {option.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </FormField>
              <FormField
                id={`asset-value-${entry.id}`}
                label="Value (required)"
              >
                <input
                  id={`asset-value-${entry.id}`}
                  inputMode="decimal"
                  value={entry.value}
                  onChange={(event) =>
                    onAssetsChange(
                      assets.map((item) =>
                        item.id === entry.id
                          ? { ...item, value: event.currentTarget.value }
                          : item,
                      ),
                    )
                  }
                />
              </FormField>
              <FormField
                id={`asset-description-${entry.id}`}
                label="Description (required for Other)"
              >
                <input
                  id={`asset-description-${entry.id}`}
                  maxLength={500}
                  value={entry.description}
                  onChange={(event) =>
                    onAssetsChange(
                      assets.map((item) =>
                        item.id === entry.id
                          ? { ...item, description: event.currentTarget.value }
                          : item,
                      ),
                    )
                  }
                />
              </FormField>
            </div>
            <Button
              type="button"
              className="button-secondary"
              onClick={() =>
                onAssetsChange(assets.filter((item) => item.id !== entry.id))
              }
            >
              Remove asset {index + 1}
            </Button>
          </section>
        ))}
        <Button
          type="button"
          className="button-secondary"
          onClick={() => onAssetsChange([...assets, emptyAsset()])}
        >
          Add an asset
        </Button>
        <label className="consent">
          <input
            type="checkbox"
            checked={assetsComplete}
            onChange={(event) =>
              onAssetsCompleteChange(event.currentTarget.checked)
            }
          />
          <span>
            I confirm this asset list is complete, including if it is empty.
          </span>
        </label>
      </fieldset>
      <fieldset>
        <legend>Liabilities</legend>
        <p>Add debts or payment obligations that apply.</p>
        {liabilities.map((entry, index) => (
          <section className="repeat-entry" key={entry.id}>
            <h3>Liability {index + 1}</h3>
            <div className="borrower-form-grid">
              <FormField
                id={`liability-type-${entry.id}`}
                label="Liability type (required)"
              >
                <select
                  id={`liability-type-${entry.id}`}
                  value={entry.liability_type}
                  onChange={(event) =>
                    onLiabilitiesChange(
                      liabilities.map((item) =>
                        item.id === entry.id
                          ? {
                              ...item,
                              liability_type: event.currentTarget.value,
                            }
                          : item,
                      ),
                    )
                  }
                >
                  <option value="">Select a type</option>
                  {[
                    "credit_card",
                    "line_of_credit",
                    "mortgage",
                    "car_loan",
                    "student_loan",
                    "personal_loan",
                    "other",
                  ].map((option) => (
                    <option value={option} key={option}>
                      {option.replaceAll("_", " ")}
                    </option>
                  ))}
                </select>
              </FormField>
              {[
                ["current_balance", "Current balance (required)"],
                ["payment_amount", "Payment amount (required)"],
              ].map(([field, label]) => (
                <FormField
                  id={`liability-${field}-${entry.id}`}
                  label={label}
                  key={field}
                >
                  <input
                    id={`liability-${field}-${entry.id}`}
                    inputMode="decimal"
                    value={entry[field as "current_balance" | "payment_amount"]}
                    onChange={(event) =>
                      onLiabilitiesChange(
                        liabilities.map((item) =>
                          item.id === entry.id
                            ? { ...item, [field]: event.currentTarget.value }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
              ))}
              <FormField
                id={`liability-frequency-${entry.id}`}
                label="Payment frequency (optional)"
              >
                <input
                  id={`liability-frequency-${entry.id}`}
                  maxLength={20}
                  value={entry.payment_frequency}
                  onChange={(event) =>
                    onLiabilitiesChange(
                      liabilities.map((item) =>
                        item.id === entry.id
                          ? {
                              ...item,
                              payment_frequency: event.currentTarget.value,
                            }
                          : item,
                      ),
                    )
                  }
                />
              </FormField>
              <FormField
                id={`liability-description-${entry.id}`}
                label="Description (required for Other)"
              >
                <input
                  id={`liability-description-${entry.id}`}
                  maxLength={500}
                  value={entry.description}
                  onChange={(event) =>
                    onLiabilitiesChange(
                      liabilities.map((item) =>
                        item.id === entry.id
                          ? { ...item, description: event.currentTarget.value }
                          : item,
                      ),
                    )
                  }
                />
              </FormField>
            </div>
            <Button
              type="button"
              className="button-secondary"
              onClick={() =>
                onLiabilitiesChange(
                  liabilities.filter((item) => item.id !== entry.id),
                )
              }
            >
              Remove liability {index + 1}
            </Button>
          </section>
        ))}
        <Button
          type="button"
          className="button-secondary"
          onClick={() =>
            onLiabilitiesChange([...liabilities, emptyLiability()])
          }
        >
          Add a liability
        </Button>
        <label className="consent">
          <input
            type="checkbox"
            checked={liabilitiesComplete}
            onChange={(event) =>
              onLiabilitiesCompleteChange(event.currentTarget.checked)
            }
          />
          <span>
            I confirm this liability list is complete, including if it is empty.
          </span>
        </label>
      </fieldset>
    </>
  );
}
