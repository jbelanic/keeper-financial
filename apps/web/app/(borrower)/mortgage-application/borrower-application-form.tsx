"use client";

import { useEffect, useRef, useState } from "react";
import { Button, LoadingState } from "@keeper/ui";
import {
  BorrowerApplicationError,
  patchBorrowerDraft,
  recoverOrStartBorrowerDraft,
  type BorrowerDraft,
  type BorrowerDraftPayload,
  type BorrowerDraftStart,
} from "@/lib/borrower-application-api";
import { AgentPreferenceSection } from "./components/agent-preference-section";
import { AssetsLiabilitiesSection } from "./components/assets-liabilities-section";
import { BorrowerDetailsSection } from "./components/borrower-details-section";
import { ConsentSection } from "./components/consent-section";
import { EmploymentIncomeSection } from "./components/employment-income-section";
import { MortgagePurposeSection } from "./components/mortgage-purpose-section";
import { NotesSection } from "./components/notes-section";
import { OtherPropertiesSection } from "./components/other-properties-section";
import { SubjectPropertySection } from "./components/subject-property-section";
import {
  emptyBorrower,
  emptyEmployment,
  type AssetState,
  type BorrowerState,
  type EmploymentState,
  type LiabilityState,
  type MortgageRequestState,
  type OtherPropertyState,
  type SubjectPropertyState,
} from "./components/types";

const steps = [
  "Mortgage request",
  "Borrowers",
  "Employment and income",
  "Assets and liabilities",
  "Subject property",
  "Other properties",
  "Notes",
  "Consent and submission",
] as const;

type DraftSummary = BorrowerDraft | BorrowerDraftStart;
type SaveState = "idle" | "saving" | "saved" | "error";

type FormApi = {
  recoverOrStart: typeof recoverOrStartBorrowerDraft;
  patch: typeof patchBorrowerDraft;
};

const defaultApi: FormApi = {
  recoverOrStart: recoverOrStartBorrowerDraft,
  patch: patchBorrowerDraft,
};

const numberOrUndefined = (value: string) =>
  value.trim() ? Number(value) : undefined;

function compact<T extends Record<string, unknown>>(record: T) {
  return Object.fromEntries(
    Object.entries(record).filter(
      ([, value]) => value !== undefined && value !== "",
    ),
  );
}

function addressPayload(value: BorrowerState["current_address"]) {
  return {
    street: value.street.trim(),
    city: value.city.trim(),
    province: value.province,
    postal_code: value.postal_code.trim(),
    years_at_address: Number(value.years_at_address),
    months_at_address: Number(value.months_at_address),
  };
}

function borrowerPayload(value: BorrowerState, includeRelationship: boolean) {
  return compact({
    first_name: value.first_name.trim(),
    last_name: value.last_name.trim(),
    email: value.email.trim(),
    phone: value.phone.trim(),
    preferred_contact_method: value.preferred_contact_method,
    date_of_birth: value.date_of_birth,
    sin: value.sin || undefined,
    marital_status: value.marital_status,
    number_of_dependants: Number(value.number_of_dependants),
    relationship_to_primary: includeRelationship
      ? value.relationship_to_primary.trim()
      : undefined,
    current_address: addressPayload(value.current_address),
  });
}

function employmentPayload(entries: EmploymentState[]) {
  return entries.map((entry) =>
    compact({
      employment_type: entry.employment_type,
      employer_name: entry.employer_name.trim() || undefined,
      job_title: entry.job_title.trim() || undefined,
      occupation_category: entry.occupation_category.trim(),
      industry: entry.industry.trim(),
      duration_years: Number(entry.duration_years),
      duration_months: Number(entry.duration_months),
      annual_gross_income: Number(entry.annual_gross_income),
      employer_address: entry.employer_address.trim() || undefined,
    }),
  );
}

function validateBorrower(
  label: string,
  value: BorrowerState,
  sinAlreadyProvided: boolean,
  coBorrower: boolean,
) {
  const errors: string[] = [];
  const required: Array<[string, string]> = [
    [value.first_name, "legal first name"],
    [value.last_name, "legal last name"],
    [value.email, "email"],
    [value.phone, "phone"],
    [value.preferred_contact_method, "preferred contact method"],
    [value.date_of_birth, "date of birth"],
    [value.marital_status, "marital status"],
    [value.current_address.street, "street address"],
    [value.current_address.city, "city"],
    [value.current_address.province, "province or territory"],
    [value.current_address.postal_code, "postal code"],
  ];
  if (coBorrower)
    required.push([value.relationship_to_primary, "relationship"]);
  required.forEach(([candidate, field]) => {
    if (!candidate.trim()) errors.push(`${label}: ${field} is required.`);
  });
  if (!sinAlreadyProvided && !/^\d{9}$/.test(value.sin)) {
    errors.push(`${label}: enter all nine SIN digits.`);
  }
  if (value.sin && !/^\d{9}$/.test(value.sin)) {
    errors.push(`${label}: replacement SIN must contain nine digits.`);
  }
  return errors;
}

function saveErrorMessages(error: unknown) {
  if (error instanceof BorrowerApplicationError) {
    if (error.status === 409) {
      return [
        "This draft changed in another request. Reload this page before saving again.",
      ];
    }
    if (error.status === 422 && error.issues.length) {
      return error.issues.map(
        (issue) =>
          `Review ${issue.path.filter((part) => part !== "body").join(" → ") || "this section"}: ${issue.message}`,
      );
    }
    if (error.status === 404) {
      return [
        "This browser can no longer access the draft. Your visible entries have not been cleared.",
      ];
    }
    if (error.status === 429) {
      return ["Too many requests. Wait briefly, then try this save again."];
    }
    if (error.status === 503) {
      return [
        "The private draft service is unavailable. Nothing was advanced or cleared.",
      ];
    }
  }
  return [
    "The section could not be saved. Check your connection and try again; your visible entries remain here.",
  ];
}

export function BorrowerApplicationForm({
  preferredAgentSlug = "",
  api = defaultApi,
}: {
  preferredAgentSlug?: string;
  api?: FormApi;
}) {
  const [draft, setDraft] = useState<DraftSummary | null>(null);
  const [recovered, setRecovered] = useState(false);
  const [startError, setStartError] = useState(false);
  const [step, setStep] = useState(0);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [errors, setErrors] = useState<string[]>([]);
  const errorRef = useRef<HTMLElement>(null);

  const [mortgage, setMortgage] = useState<MortgageRequestState>({
    mortgage_objective: "",
    requested_amount: "",
    estimated_property_value: "",
    expected_closing_date: "",
    preferred_agent_slug: preferredAgentSlug,
    down_payment_sources: [],
  });
  const [primary, setPrimary] = useState<BorrowerState>(emptyBorrower);
  const [coBorrower, setCoBorrower] = useState<BorrowerState | null>(null);
  const [primaryEmployment, setPrimaryEmployment] = useState<EmploymentState[]>(
    [emptyEmployment()],
  );
  const [coEmployment, setCoEmployment] = useState<EmploymentState[] | null>(
    null,
  );
  const [assets, setAssets] = useState<AssetState[]>([]);
  const [liabilities, setLiabilities] = useState<LiabilityState[]>([]);
  const [assetsComplete, setAssetsComplete] = useState(false);
  const [liabilitiesComplete, setLiabilitiesComplete] = useState(false);
  const [subjectProperty, setSubjectProperty] = useState<SubjectPropertyState>({
    identified: false,
    address: "",
    city: "",
    province: "",
    postal_code: "",
    property_type: "",
    property_style: "",
    occupancy: "",
    year_built: "",
    livable_area_sqft: "",
    units: "",
    monthly_property_tax: "",
    monthly_heating_cost: "",
    monthly_condo_fee: "",
    lot_details: "",
    garage_details: "",
  });
  const [otherProperties, setOtherProperties] = useState<OtherPropertyState[]>(
    [],
  );
  const [notes, setNotes] = useState("");
  const [consentAcknowledged, setConsentAcknowledged] = useState(false);
  const hasSavedSin = Boolean(draft && "has_sin" in draft && draft.has_sin);
  const hasSavedCoBorrower = Boolean(
    draft && "has_co_borrower" in draft && draft.has_co_borrower,
  );

  useEffect(() => {
    let active = true;
    api
      .recoverOrStart()
      .then(({ draft: nextDraft, recovered: wasRecovered }) => {
        if (!active) return;
        setDraft(nextDraft);
        setRecovered(wasRecovered);
        if (
          wasRecovered &&
          "has_co_borrower" in nextDraft &&
          nextDraft.has_co_borrower
        ) {
          setCoBorrower(emptyBorrower());
          setCoEmployment([emptyEmployment()]);
        }
      })
      .catch(() => {
        if (active) setStartError(true);
      });
    return () => {
      active = false;
    };
  }, [api]);

  useEffect(() => {
    if (errors.length) errorRef.current?.focus();
  }, [errors]);

  async function saveSection(
    payload: BorrowerDraftPayload,
    validationErrors: string[] = [],
  ) {
    if (!draft || validationErrors.length) {
      setErrors(
        validationErrors.length
          ? validationErrors
          : ["The private draft is not ready. Try again shortly."],
      );
      return;
    }
    setErrors([]);
    setSaveState("saving");
    try {
      const saved = await api.patch(
        draft.application_id,
        draft.revision,
        payload,
      );
      setDraft(saved);
      setSaveState("saved");
      setStep((current) => Math.min(current + 1, steps.length - 1));
      window.requestAnimationFrame(() => {
        document.querySelector<HTMLElement>("#borrower-step-heading")?.focus();
      });
    } catch (error) {
      setSaveState("error");
      setErrors(saveErrorMessages(error));
    }
  }

  if (!draft && !startError) {
    return (
      <div className="container borrower-page">
        <LoadingState label="Preparing your private draft" />
      </div>
    );
  }

  if (startError || !draft) {
    return (
      <div className="container borrower-page">
        <section className="error-state" role="alert">
          <h1>We could not prepare a private draft</h1>
          <p>
            No application information was stored. Refresh to try again or
            return to the public Get started page.
          </p>
        </section>
      </div>
    );
  }

  const section = (() => {
    if (step === 0) {
      return <MortgagePurposeSection value={mortgage} onChange={setMortgage} />;
    }
    if (step === 1) {
      return (
        <BorrowerDetailsSection
          primary={primary}
          coBorrower={coBorrower}
          hasSavedPrimarySin={hasSavedSin}
          hasSavedCoBorrower={hasSavedCoBorrower}
          onPrimaryChange={setPrimary}
          onCoBorrowerChange={setCoBorrower}
          onAddCoBorrower={() => {
            setCoBorrower(emptyBorrower());
            setCoEmployment([emptyEmployment()]);
          }}
          onRemoveCoBorrower={() => {
            setCoBorrower(null);
            setCoEmployment(null);
          }}
        />
      );
    }
    if (step === 2) {
      return (
        <EmploymentIncomeSection
          primary={primaryEmployment}
          coBorrower={coBorrower ? (coEmployment ?? [emptyEmployment()]) : null}
          onPrimaryChange={setPrimaryEmployment}
          onCoBorrowerChange={setCoEmployment}
        />
      );
    }
    if (step === 3) {
      return (
        <AssetsLiabilitiesSection
          assets={assets}
          liabilities={liabilities}
          assetsComplete={assetsComplete}
          liabilitiesComplete={liabilitiesComplete}
          onAssetsChange={setAssets}
          onLiabilitiesChange={setLiabilities}
          onAssetsCompleteChange={setAssetsComplete}
          onLiabilitiesCompleteChange={setLiabilitiesComplete}
        />
      );
    }
    if (step === 4) {
      return (
        <SubjectPropertySection
          value={subjectProperty}
          onChange={setSubjectProperty}
        />
      );
    }
    if (step === 5) {
      return (
        <OtherPropertiesSection
          properties={otherProperties}
          onChange={setOtherProperties}
        />
      );
    }
    if (step === 6) {
      return <NotesSection value={notes} onChange={setNotes} />;
    }
    return (
      <ConsentSection
        acknowledged={consentAcknowledged}
        onChange={setConsentAcknowledged}
      />
    );
  })();

  function currentSave() {
    if (step === 0) {
      const validation: string[] = [];
      if (!mortgage.mortgage_objective) {
        validation.push("Select a mortgage purpose.");
      }
      if (
        ["purchase", "refinance"].includes(mortgage.mortgage_objective) &&
        !mortgage.requested_amount &&
        !mortgage.estimated_property_value
      ) {
        validation.push(
          "Enter a requested amount or estimated property value for this purpose.",
        );
      }
      return saveSection(
        {
          mortgage_request: compact({
            mortgage_objective: mortgage.mortgage_objective,
            requested_amount: numberOrUndefined(mortgage.requested_amount),
            estimated_property_value: numberOrUndefined(
              mortgage.estimated_property_value,
            ),
            expected_closing_date: mortgage.expected_closing_date || undefined,
            preferred_agent_slug: mortgage.preferred_agent_slug || undefined,
            down_payment_sources: mortgage.down_payment_sources.map((source) =>
              compact({
                source: source.source,
                amount: Number(source.amount),
                description: source.description || undefined,
              }),
            ),
          }),
        },
        validation,
      );
    }
    if (step === 1) {
      const validation = [
        ...validateBorrower("Primary borrower", primary, hasSavedSin, false),
        ...(coBorrower
          ? validateBorrower(
              "Co-borrower",
              coBorrower,
              hasSavedCoBorrower,
              true,
            )
          : []),
      ];
      return saveSection(
        {
          primary_borrower: borrowerPayload(primary, false),
          co_borrower: coBorrower ? borrowerPayload(coBorrower, true) : null,
        },
        validation,
      );
    }
    if (step === 2) {
      const allEntries = [
        ...primaryEmployment.map(
          (entry) => ["Primary borrower", entry] as const,
        ),
        ...(coEmployment ?? []).map((entry) => ["Co-borrower", entry] as const),
      ];
      const validation = allEntries.flatMap(([label, entry], index) => {
        const missing =
          !entry.employment_type ||
          !entry.occupation_category.trim() ||
          !entry.industry.trim() ||
          !entry.annual_gross_income.trim();
        return missing
          ? [`${label} income entry ${index + 1} is missing a required value.`]
          : [];
      });
      return saveSection(
        {
          primary_borrower: {
            employment: employmentPayload(primaryEmployment),
          },
          ...(coBorrower
            ? {
                co_borrower: {
                  employment: employmentPayload(coEmployment ?? []),
                },
              }
            : {}),
        },
        validation,
      );
    }
    if (step === 3) {
      return saveSection(
        {
          assets: assets.map((asset) =>
            compact({
              asset_type: asset.asset_type,
              value: Number(asset.value),
              description: asset.description || undefined,
            }),
          ),
          assets_complete: assetsComplete,
          liabilities: liabilities.map((liability) =>
            compact({
              liability_type: liability.liability_type,
              current_balance: Number(liability.current_balance),
              payment_amount: Number(liability.payment_amount),
              payment_frequency: liability.payment_frequency || undefined,
              description: liability.description || undefined,
            }),
          ),
          liabilities_complete: liabilitiesComplete,
        },
        [
          ...(!assetsComplete
            ? ["Confirm whether the asset list is complete."]
            : []),
          ...(!liabilitiesComplete
            ? ["Confirm whether the liability list is complete."]
            : []),
        ],
      );
    }
    if (step === 4) {
      const validation =
        subjectProperty.identified &&
        (!subjectProperty.address ||
          !subjectProperty.city ||
          !subjectProperty.province ||
          !subjectProperty.postal_code ||
          !subjectProperty.property_type ||
          !subjectProperty.property_style ||
          !subjectProperty.occupancy)
          ? ["Complete the required identified-property fields."]
          : [];
      return saveSection(
        {
          subject_property: subjectProperty.identified
            ? compact({
                address: subjectProperty.address,
                city: subjectProperty.city,
                province: subjectProperty.province,
                postal_code: subjectProperty.postal_code,
                property_type: subjectProperty.property_type,
                property_style: subjectProperty.property_style,
                occupancy: subjectProperty.occupancy,
                year_built: numberOrUndefined(subjectProperty.year_built),
                livable_area_sqft: numberOrUndefined(
                  subjectProperty.livable_area_sqft,
                ),
                units: numberOrUndefined(subjectProperty.units),
                monthly_property_tax: numberOrUndefined(
                  subjectProperty.monthly_property_tax,
                ),
                monthly_heating_cost: numberOrUndefined(
                  subjectProperty.monthly_heating_cost,
                ),
                monthly_condo_fee: numberOrUndefined(
                  subjectProperty.monthly_condo_fee,
                ),
                lot_details: subjectProperty.lot_details || undefined,
                garage_details: subjectProperty.garage_details || undefined,
              })
            : null,
        },
        validation,
      );
    }
    if (step === 5) {
      return saveSection({
        other_properties: otherProperties.map((property) => ({
          address: property.address || undefined,
          purchase_date: property.purchase_date || undefined,
          purchase_price: numberOrUndefined(property.purchase_price),
          estimated_value: numberOrUndefined(property.estimated_value),
          is_owner_occupied: property.is_owner_occupied,
          mortgages: property.mortgages.map((mortgage) =>
            compact({
              balance: Number(mortgage.balance),
              payment_amount: Number(mortgage.payment_amount),
              payment_frequency: mortgage.payment_frequency,
              maturity_date: mortgage.maturity_date || undefined,
            }),
          ),
        })),
      });
    }
    if (step === 6) {
      return saveSection({ additional_notes: notes || null });
    }
  }

  return (
    <div className="container borrower-page">
      <header className="borrower-intro">
        <p className="eyebrow">Same-browser private draft</p>
        <h1>Mortgage application</h1>
        <p>
          Save one section at a time. Your answers stay in encrypted server
          state; this page does not place them in browser storage, URLs,
          analytics, or server-rendered markup.
        </p>
        <p className="notice">
          Do not use a shared device. This draft can resume only while this
          browser retains its secure capability cookie. Final submission and
          document upload are deferred to the next implementation phase.
        </p>
        {recovered ? (
          <p className="save-feedback save-feedback-saved" role="status">
            Existing private draft recovered. Saved SIN is shown only as
            provided/masked state; other answers are not returned to this page.
          </p>
        ) : null}
      </header>
      <AgentPreferenceSection slug={preferredAgentSlug} />
      <nav className="progress-nav" aria-label="Application sections">
        <p className="progress-nav-title">
          Section {step + 1} of {steps.length}
        </p>
        <ol>
          {steps.map((label, index) => (
            <li key={label}>
              {index === step ? (
                <strong aria-current="step">{label}</strong>
              ) : index < step ? (
                <button type="button" onClick={() => setStep(index)}>
                  {label} — saved
                </button>
              ) : (
                <span>{label}</span>
              )}
            </li>
          ))}
        </ol>
      </nav>
      {errors.length ? (
        <section
          className="error-summary"
          role="alert"
          tabIndex={-1}
          ref={errorRef}
          aria-labelledby="borrower-error-heading"
        >
          <h2 id="borrower-error-heading">This section was not saved</h2>
          <ul>
            {errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </section>
      ) : null}
      <section aria-labelledby="borrower-step-heading">
        <h2 id="borrower-step-heading" tabIndex={-1}>
          {steps[step]}
        </h2>
        {section}
      </section>
      <div className="application-actions">
        <div className="button-row">
          {step > 0 ? (
            <Button
              type="button"
              className="button-secondary"
              disabled={saveState === "saving"}
              onClick={() => {
                setErrors([]);
                setStep((current) => current - 1);
              }}
            >
              Back
            </Button>
          ) : null}
          {step < steps.length - 1 ? (
            <Button
              type="button"
              disabled={saveState === "saving"}
              onClick={() => void currentSave()}
            >
              {saveState === "saving" ? "Saving…" : "Save and continue"}
            </Button>
          ) : (
            <Button
              type="button"
              disabled
              aria-describedby="submission-deferred"
            >
              Submit application — coming in Phase D
            </Button>
          )}
        </div>
        <p
          className={`save-feedback save-feedback-${saveState}`}
          aria-live="polite"
        >
          {saveState === "saving"
            ? "Saving this section securely…"
            : saveState === "saved"
              ? "Section saved securely."
              : saveState === "error"
                ? "Nothing was advanced or cleared."
                : ""}
        </p>
        {step === steps.length - 1 ? (
          <p id="submission-deferred" className="notice">
            Final submission is deliberately unavailable in Phase C. No submit
            endpoint is called, even after acknowledging the synthetic draft
            consent wording.
          </p>
        ) : null}
      </div>
    </div>
  );
}
