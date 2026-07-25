import { Button, FormField } from "@keeper/ui";
import { emptyEmployment, type EmploymentState } from "./types";

function EmploymentList({
  borrowerLabel,
  prefix,
  entries,
  onChange,
}: {
  borrowerLabel: string;
  prefix: string;
  entries: EmploymentState[];
  onChange: (entries: EmploymentState[]) => void;
}) {
  const update = (index: number, field: keyof EmploymentState, value: string) =>
    onChange(
      entries.map((entry, entryIndex) =>
        entryIndex === index ? { ...entry, [field]: value } : entry,
      ),
    );
  return (
    <fieldset>
      <legend>{borrowerLabel} employment and income</legend>
      <p>
        At least one current income or employment entry is required. This is
        borrower-declared information and is not automatically verified.
      </p>
      {entries.map((entry, index) => (
        <section className="repeat-entry" key={entry.id}>
          <h3>
            {borrowerLabel} income entry {index + 1}
          </h3>
          <div className="borrower-form-grid">
            <FormField
              id={`${prefix}-employment-type-${entry.id}`}
              label="Employment or income type (required)"
            >
              <select
                id={`${prefix}-employment-type-${entry.id}`}
                value={entry.employment_type}
                onChange={(event) =>
                  update(index, "employment_type", event.currentTarget.value)
                }
              >
                <option value="">Select a type</option>
                <option value="employed">Employed</option>
                <option value="self_employed">Self-employed</option>
                <option value="retired">Retired</option>
                <option value="other_income">Other income</option>
              </select>
            </FormField>
            <FormField
              id={`${prefix}-employer-${entry.id}`}
              label="Employer or business name (required when applicable)"
            >
              <input
                id={`${prefix}-employer-${entry.id}`}
                maxLength={200}
                value={entry.employer_name}
                onChange={(event) =>
                  update(index, "employer_name", event.currentTarget.value)
                }
              />
            </FormField>
            <FormField
              id={`${prefix}-job-title-${entry.id}`}
              label="Job title (required when applicable)"
            >
              <input
                id={`${prefix}-job-title-${entry.id}`}
                maxLength={200}
                value={entry.job_title}
                onChange={(event) =>
                  update(index, "job_title", event.currentTarget.value)
                }
              />
            </FormField>
            <FormField
              id={`${prefix}-occupation-${entry.id}`}
              label="Occupation or category (required)"
            >
              <input
                id={`${prefix}-occupation-${entry.id}`}
                maxLength={100}
                value={entry.occupation_category}
                onChange={(event) =>
                  update(
                    index,
                    "occupation_category",
                    event.currentTarget.value,
                  )
                }
              />
            </FormField>
            <FormField
              id={`${prefix}-industry-${entry.id}`}
              label="Industry (required)"
            >
              <input
                id={`${prefix}-industry-${entry.id}`}
                maxLength={100}
                value={entry.industry}
                onChange={(event) =>
                  update(index, "industry", event.currentTarget.value)
                }
              />
            </FormField>
            <FormField
              id={`${prefix}-duration-years-${entry.id}`}
              label="Years (required)"
            >
              <input
                id={`${prefix}-duration-years-${entry.id}`}
                type="number"
                min="0"
                max="100"
                value={entry.duration_years}
                onChange={(event) =>
                  update(index, "duration_years", event.currentTarget.value)
                }
              />
            </FormField>
            <FormField
              id={`${prefix}-duration-months-${entry.id}`}
              label="Additional months (required)"
            >
              <input
                id={`${prefix}-duration-months-${entry.id}`}
                type="number"
                min="0"
                max="11"
                value={entry.duration_months}
                onChange={(event) =>
                  update(index, "duration_months", event.currentTarget.value)
                }
              />
            </FormField>
            <FormField
              id={`${prefix}-income-${entry.id}`}
              label="Annual gross income (required)"
            >
              <input
                id={`${prefix}-income-${entry.id}`}
                inputMode="decimal"
                value={entry.annual_gross_income}
                onChange={(event) =>
                  update(
                    index,
                    "annual_gross_income",
                    event.currentTarget.value,
                  )
                }
              />
            </FormField>
            <FormField
              id={`${prefix}-employer-address-${entry.id}`}
              label="Employer address (optional)"
            >
              <input
                id={`${prefix}-employer-address-${entry.id}`}
                maxLength={200}
                value={entry.employer_address}
                onChange={(event) =>
                  update(index, "employer_address", event.currentTarget.value)
                }
              />
            </FormField>
          </div>
          {entries.length > 1 ? (
            <Button
              type="button"
              className="button-secondary"
              onClick={() =>
                onChange(
                  entries.filter((candidate) => candidate.id !== entry.id),
                )
              }
            >
              Remove {borrowerLabel.toLowerCase()} income entry {index + 1}
            </Button>
          ) : null}
        </section>
      ))}
      {entries.length < 5 ? (
        <Button
          type="button"
          className="button-secondary"
          onClick={() => onChange([...entries, emptyEmployment()])}
        >
          Add another {borrowerLabel.toLowerCase()} income entry
        </Button>
      ) : null}
    </fieldset>
  );
}

export function EmploymentIncomeSection({
  primary,
  coBorrower,
  onPrimaryChange,
  onCoBorrowerChange,
}: {
  primary: EmploymentState[];
  coBorrower: EmploymentState[] | null;
  onPrimaryChange: (entries: EmploymentState[]) => void;
  onCoBorrowerChange: (entries: EmploymentState[]) => void;
}) {
  return (
    <>
      <EmploymentList
        borrowerLabel="Primary borrower"
        prefix="primary"
        entries={primary}
        onChange={onPrimaryChange}
      />
      {coBorrower ? (
        <EmploymentList
          borrowerLabel="Co-borrower"
          prefix="co"
          entries={coBorrower}
          onChange={onCoBorrowerChange}
        />
      ) : null}
    </>
  );
}
