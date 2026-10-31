"use client";

import { useEffect, useRef, useState } from "react";
import { Button, LoadingState } from "@keeper/ui";
import {
  BorrowerApplicationError,
  forgetBorrowerApplicationId,
  getBorrowerConsent,
  patchBorrowerDraft,
  recoverOrStartBorrowerDraft,
  submitBorrowerApplication,
  type BorrowerConsent,
  type BorrowerDraft,
  type BorrowerDraftPayload,
  type BorrowerRecoveredDraft,
  type BorrowerDraftStart,
} from "@/lib/borrower-application-api";
import { AgentPreferenceSection } from "./components/agent-preference-section";
import { AssetsLiabilitiesSection } from "./components/assets-liabilities-section";
import { BorrowerDetailsSection } from "./components/borrower-details-section";
import { ConsentSection } from "./components/consent-section";
import { DocumentUpload } from "./components/document-upload";
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
import { hydrateBorrowerDraft } from "./draft-hydration";
import {
  fieldMessages,
  issueLines,
  validateAssetsAndLiabilities,
  validateBorrowerDetails,
  validateEmploymentEntries,
  validateMortgageRequest,
  validateOtherProperties,
  validateSubjectProperty,
  type FieldIssue,
} from "./section-validation";
import {
  humaniseIssueMessage,
  issueSummary,
  type BorrowerIssue,
} from "@/lib/validation-issues";
import { numberValue } from "@/lib/number-input";
import { formatRelativeTime } from "@/lib/relative-time";

const steps = [
  "Mortgage request",
  "Borrowers",
  "Employment and income",
  "Assets and liabilities",
  "Subject property",
  "Other properties",
  "Notes",
  "Documents",
  "Consent and submission",
] as const;

type DraftSummary = BorrowerDraft | BorrowerRecoveredDraft | BorrowerDraftStart;
type SaveState = "idle" | "saving" | "saved" | "error";

type FormApi = {
  recoverOrStart: typeof recoverOrStartBorrowerDraft;
  patch: typeof patchBorrowerDraft;
  getConsent?: typeof getBorrowerConsent;
  submit?: typeof submitBorrowerApplication;
};

const defaultApi: FormApi = {
  recoverOrStart: recoverOrStartBorrowerDraft,
  patch: patchBorrowerDraft,
  getConsent: getBorrowerConsent,
  submit: submitBorrowerApplication,
};

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
    years_at_address: numberValue(value.years_at_address, "integer"),
    months_at_address: numberValue(value.months_at_address, "integer"),
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
    number_of_dependants: numberValue(value.number_of_dependants, "integer"),
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
      duration_years: numberValue(entry.duration_years, "integer"),
      duration_months: numberValue(entry.duration_months, "integer"),
      annual_gross_income: numberValue(entry.annual_gross_income),
      employer_address: entry.employer_address.trim() || undefined,
    }),
  );
}

type SaveFailure = {
  /** Ready-to-show summary lines: never an internal path or library wording. */
  summary: string[];
  /** The rejected fields, so the section can mark the input itself. */
  issues: BorrowerIssue[];
};

function saveFailure(error: unknown): SaveFailure {
  if (error instanceof BorrowerApplicationError) {
    if (error.status === 409) {
      return {
        summary: [
          "This draft changed in another request. Reload this page before saving again.",
        ],
        issues: [],
      };
    }
    if (error.status === 422 && error.issues.length) {
      return {
        summary: error.issues.map(issueSummary),
        issues: error.issues,
      };
    }
    if (error.status === 422 && error.code === "payload_incomplete") {
      return {
        summary: [
          "The saved application is missing required information. Go back through the sections, fill in what is marked, and save each section again before submitting.",
        ],
        issues: [],
      };
    }
    if (error.status === 422) {
      return {
        summary: [
          "The saved application could not be submitted. Check the consent acknowledgement and try again.",
        ],
        issues: [],
      };
    }
    if (error.status === 404) {
      return {
        summary: [
          "This browser can no longer access the draft. Your visible entries have not been cleared.",
        ],
        issues: [],
      };
    }
    if (error.status === 429) {
      return {
        summary: ["Too many requests. Wait briefly, then try this save again."],
        issues: [],
      };
    }
    if (error.status === 503) {
      return {
        summary: [
          "The private draft service is unavailable. Nothing was advanced or cleared.",
        ],
        issues: [],
      };
    }
  }
  return {
    summary: [
      "The section could not be saved. Check your connection and try again; your visible entries remain here.",
    ],
    issues: [],
  };
}

const MORTGAGE_FIELD_IDS: Record<string, string> = {
  mortgage_objective: "mortgage-objective",
  requested_amount: "requested-amount",
  estimated_property_value: "estimated-property-value",
  expected_closing_date: "expected-closing-date",
};

const BORROWER_FIELD_IDS: Record<string, string> = {
  first_name: "first-name",
  last_name: "last-name",
  email: "email",
  phone: "phone",
  preferred_contact_method: "contact",
  date_of_birth: "dob",
  sin: "sin",
  marital_status: "marital",
  number_of_dependants: "dependants",
  relationship_to_primary: "relationship",
};

const ADDRESS_FIELD_IDS: Record<string, string> = {
  street: "street",
  city: "city",
  province: "province",
  postal_code: "postal",
  years_at_address: "address-years",
  months_at_address: "address-months",
};

const EMPLOYMENT_FIELD_IDS: Record<string, string> = {
  employment_type: "employment-type",
  employer_name: "employer",
  job_title: "job-title",
  occupation_category: "occupation",
  industry: "industry",
  duration_years: "duration-years",
  duration_months: "duration-months",
  annual_gross_income: "income",
  employer_address: "employer-address",
};

const SUBJECT_FIELD_IDS: Record<string, string> = {
  address: "address",
  city: "city",
  province: "province",
  postal_code: "postal",
  property_type: "type",
  property_style: "style",
  occupancy: "occupancy",
  year_built: "year_built",
  livable_area_sqft: "livable_area_sqft",
  units: "units",
  monthly_property_tax: "monthly_property_tax",
  monthly_heating_cost: "monthly_heating_cost",
  monthly_condo_fee: "monthly_condo_fee",
  lot_details: "lot-details",
  garage_details: "garage-details",
};

type IssueLookupState = {
  downPaymentSources: MortgageRequestState["down_payment_sources"];
  primaryEmployment: EmploymentState[];
  coEmployment: EmploymentState[] | null;
  assets: AssetState[];
  liabilities: LiabilityState[];
  otherProperties: OtherPropertyState[];
};

/**
 * The DOM id of the input an issue belongs to, so the message can sit beside it.
 *
 * Repeatable rows carry a client-generated id rather than an index, so the
 * current state is needed to translate `assets[0].value` into `asset-value-…`.
 */
export function fieldIdForIssue(
  path: Array<string | number>,
  state: IssueLookupState,
): string | null {
  const parts = path.filter((part) => part !== "body");
  const at = (index: number) =>
    typeof parts[index] === "number" ? (parts[index] as number) : undefined;

  if (parts[0] === "mortgage_request") {
    if (parts[1] === "down_payment_sources") {
      const entry = state.downPaymentSources[at(2) ?? -1];
      if (!entry) return null;
      if (parts[3] === "amount") return `down-payment-amount-${entry.id}`;
      if (parts[3] === "source") return `down-payment-source-${entry.id}`;
      if (parts[3] === "description") {
        return `down-payment-description-${entry.id}`;
      }
      return null;
    }
    return MORTGAGE_FIELD_IDS[String(parts[1])] ?? null;
  }

  if (parts[0] === "primary_borrower" || parts[0] === "co_borrower") {
    const prefix = parts[0] === "primary_borrower" ? "primary" : "co";
    if (parts[1] === "current_address") {
      const suffix = ADDRESS_FIELD_IDS[String(parts[2])];
      return suffix ? `${prefix}-${suffix}` : null;
    }
    if (parts[1] === "employment") {
      const entries =
        parts[0] === "primary_borrower"
          ? state.primaryEmployment
          : (state.coEmployment ?? []);
      const entry = entries[at(2) ?? -1];
      const suffix = EMPLOYMENT_FIELD_IDS[String(parts[3])];
      return entry && suffix ? `${prefix}-${suffix}-${entry.id}` : null;
    }
    const suffix = BORROWER_FIELD_IDS[String(parts[1])];
    return suffix ? `${prefix}-${suffix}` : null;
  }

  if (parts[0] === "assets") {
    const entry = state.assets[at(1) ?? -1];
    if (!entry) return null;
    if (parts[2] === "value") return `asset-value-${entry.id}`;
    if (parts[2] === "asset_type") return `asset-type-${entry.id}`;
    if (parts[2] === "description") return `asset-description-${entry.id}`;
    return null;
  }

  if (parts[0] === "liabilities") {
    const entry = state.liabilities[at(1) ?? -1];
    if (!entry) return null;
    if (parts[2] === "current_balance") {
      return `liability-current_balance-${entry.id}`;
    }
    if (parts[2] === "payment_amount") {
      return `liability-payment_amount-${entry.id}`;
    }
    if (parts[2] === "payment_frequency") {
      return `liability-frequency-${entry.id}`;
    }
    if (parts[2] === "description") {
      return `liability-description-${entry.id}`;
    }
    return null;
  }

  if (parts[0] === "subject_property") {
    const suffix = SUBJECT_FIELD_IDS[String(parts[1])];
    return suffix ? `subject-${suffix}` : null;
  }

  if (parts[0] === "other_properties") {
    const entry = state.otherProperties[at(1) ?? -1];
    if (!entry) return null;
    if (parts[2] === "mortgages") {
      const mortgage = entry.mortgages[at(3) ?? -1];
      const field = String(parts[4]);
      return mortgage && field
        ? `other-mortgage-${field}-${mortgage.id}`
        : null;
    }
    const suffix = String(parts[2]);
    return suffix && suffix !== "undefined"
      ? `other-${suffix}-${entry.id}`
      : null;
  }

  return null;
}

/** Field messages keyed by DOM id, first message wins for a repeated field. */
function fieldErrorsFor(
  issues: BorrowerIssue[],
  state: IssueLookupState,
): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const issue of issues) {
    const id = fieldIdForIssue(issue.path, state);
    if (!id || errors[id]) continue;
    errors[id] = humaniseIssueMessage(issue.message);
  }
  return errors;
}

export function BorrowerApplicationForm({
  agentCode = "",
  api = defaultApi,
}: {
  agentCode?: string;
  api?: FormApi;
}) {
  const [draft, setDraft] = useState<DraftSummary | null>(null);
  const [recovered, setRecovered] = useState(false);
  const [restoredData, setRestoredData] = useState(false);
  const [startError, setStartError] = useState(false);
  const [attributedAgentName, setAttributedAgentName] = useState<string | null>(
    null,
  );
  const [step, setStep] = useState(0);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [errors, setErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [errorTitle, setErrorTitle] = useState("This section was not saved");
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const errorRef = useRef<HTMLElement>(null);

  const [mortgage, setMortgage] = useState<MortgageRequestState>({
    mortgage_objective: "",
    requested_amount: "",
    estimated_property_value: "",
    expected_closing_date: "",
    preferred_agent_slug: "",
    preferred_agent_name: "",
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
  const [consent, setConsent] = useState<BorrowerConsent | null>(null);
  const [documentsSettled, setDocumentsSettled] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const hasSavedSin = Boolean(draft && "has_sin" in draft && draft.has_sin);
  const hasSavedCoBorrower = Boolean(
    draft && "has_co_borrower" in draft && draft.has_co_borrower,
  );

  useEffect(() => {
    let active = true;
    api
      .recoverOrStart(agentCode)
      .then(({ draft: nextDraft, recovered: wasRecovered }) => {
        if (!active) return;
        setDraft(nextDraft);
        setRecovered(wasRecovered);
        setAttributedAgentName(
          "attributed_agent_name" in nextDraft
            ? (nextDraft.attributed_agent_name ?? null)
            : null,
        );
        if (
          wasRecovered &&
          "payload" in nextDraft &&
          nextDraft.payload !== null &&
          typeof nextDraft.payload === "object" &&
          !Array.isArray(nextDraft.payload)
        ) {
          const restored = hydrateBorrowerDraft(
            nextDraft.payload as Record<string, unknown>,
            "",
          );
          setMortgage(restored.mortgage);
          setPrimary(restored.primary);
          setCoBorrower(restored.coBorrower);
          setPrimaryEmployment(restored.primaryEmployment);
          setCoEmployment(restored.coEmployment);
          setAssets(restored.assets);
          setLiabilities(restored.liabilities);
          setAssetsComplete(restored.assetsComplete);
          setLiabilitiesComplete(restored.liabilitiesComplete);
          setSubjectProperty(restored.subjectProperty);
          setOtherProperties(restored.otherProperties);
          setNotes(restored.notes);
          setStep(restored.resumeStep);
          setRestoredData(Object.keys(nextDraft.payload).length > 0);
        }
        (api.getConsent ?? getBorrowerConsent)(nextDraft.application_id)
          .then((value) => {
            if (active) setConsent(value);
          })
          .catch(() => {
            if (active)
              setErrors(["Current consent wording could not be loaded."]);
          });
        if (
          wasRecovered &&
          !("payload" in nextDraft && nextDraft.payload) &&
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
  }, [api, agentCode]);

  useEffect(() => {
    if (errors.length) errorRef.current?.focus();
  }, [errors]);

  // Keep "saved N minutes ago" honest without re-rendering on every keystroke.
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 30_000);
    return () => window.clearInterval(timer);
  }, []);

  function issueState(): IssueLookupState {
    return {
      downPaymentSources: mortgage.down_payment_sources,
      primaryEmployment,
      coEmployment,
      assets,
      liabilities,
      otherProperties,
    };
  }

  /** Every problem in one step, each pointing at the control that needs it. */
  function sectionIssues(index: number): FieldIssue[] {
    if (index === 0) return validateMortgageRequest(mortgage);
    if (index === 1) {
      return [
        ...validateBorrowerDetails(
          "primary",
          "Primary borrower",
          primary,
          hasSavedSin,
          false,
        ),
        ...(coBorrower
          ? validateBorrowerDetails(
              "co",
              "Co-borrower",
              coBorrower,
              hasSavedCoBorrower,
              true,
            )
          : []),
      ];
    }
    if (index === 2) {
      return [
        ...validateEmploymentEntries(
          "primary",
          "Primary borrower",
          primaryEmployment,
        ),
        ...(coBorrower
          ? validateEmploymentEntries("co", "Co-borrower", coEmployment ?? [])
          : []),
      ];
    }
    if (index === 3) {
      return validateAssetsAndLiabilities(
        assets,
        liabilities,
        assetsComplete,
        liabilitiesComplete,
      );
    }
    if (index === 4) return validateSubjectProperty(subjectProperty);
    if (index === 5) return validateOtherProperties(otherProperties);
    return [];
  }

  /** Put the cursor in the field that needs an answer, once it has rendered. */
  function focusField(field: string | undefined) {
    if (!field) return;
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        const control = document.getElementById(field);
        if (!control) return;
        control.scrollIntoView?.({ block: "center", behavior: "smooth" });
        control.focus({ preventScroll: true });
      });
    });
  }

  /** Mark the controls, then move focus to the first one that needs an answer. */
  function blockOn(issues: FieldIssue[], title: string) {
    setErrorTitle(title);
    setFieldErrors(fieldMessages(issues));
    setErrors(issueLines(issues));
    focusField(issues[0]?.field);
  }

  /** Every section that would fail a submission, in form order. */
  function incompleteSections() {
    return steps
      .map((_, index) => ({ index, issues: sectionIssues(index) }))
      .filter((entry) => entry.issues.length > 0);
  }

  async function saveSection(
    payload: BorrowerDraftPayload,
    issues: FieldIssue[] = [],
  ) {
    if (!draft || issues.length) {
      if (issues.length) {
        blockOn(issues, "This section needs a few answers");
      } else {
        setErrorTitle("This section was not saved");
        setFieldErrors({});
        setErrors(["The private draft is not ready. Try again shortly."]);
      }
      return;
    }
    setErrors([]);
    setFieldErrors({});
    setErrorTitle("This section was not saved");
    setSaveState("saving");
    try {
      const saved = await api.patch(
        draft.application_id,
        draft.revision,
        payload,
      );
      setDraft(saved);
      setSaveState("saved");
      setSavedAt(Date.now());
      setStep((current) => Math.min(current + 1, steps.length - 1));
      window.requestAnimationFrame(() => {
        document.querySelector<HTMLElement>("#borrower-step-heading")?.focus();
      });
    } catch (error) {
      setSaveState("error");
      const failure = saveFailure(error);
      setErrors(failure.summary);
      setFieldErrors(fieldErrorsFor(failure.issues, issueState()));
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
      return (
        <MortgagePurposeSection
          value={mortgage}
          onChange={setMortgage}
          fieldErrors={fieldErrors}
        />
      );
    }
    if (step === 1) {
      return (
        <BorrowerDetailsSection
          fieldErrors={fieldErrors}
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
          fieldErrors={fieldErrors}
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
          fieldErrors={fieldErrors}
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
          fieldErrors={fieldErrors}
          value={subjectProperty}
          onChange={setSubjectProperty}
        />
      );
    }
    if (step === 5) {
      return (
        <OtherPropertiesSection
          fieldErrors={fieldErrors}
          properties={otherProperties}
          onChange={setOtherProperties}
        />
      );
    }
    if (step === 6) {
      return <NotesSection value={notes} onChange={setNotes} />;
    }
    if (step === 7) {
      return (
        <DocumentUpload
          applicationId={draft.application_id}
          onSettledChange={setDocumentsSettled}
        />
      );
    }
    return (
      <ConsentSection
        wording={
          consent?.wording_text ?? "Current consent wording is unavailable."
        }
        version={consent?.consent_version ?? "unavailable"}
        acknowledged={consentAcknowledged}
        onChange={setConsentAcknowledged}
      />
    );
  })();

  function currentSave() {
    if (step === 0) {
      return saveSection(
        {
          mortgage_request: compact({
            mortgage_objective: mortgage.mortgage_objective,
            requested_amount: numberValue(mortgage.requested_amount),
            estimated_property_value: numberValue(
              mortgage.estimated_property_value,
            ),
            expected_closing_date: mortgage.expected_closing_date || undefined,
            preferred_agent_name:
              mortgage.preferred_agent_name.trim() || undefined,
            down_payment_sources: mortgage.down_payment_sources.map((source) =>
              compact({
                source: source.source,
                amount: numberValue(source.amount),
                description: source.description || undefined,
              }),
            ),
          }),
        },
        sectionIssues(0),
      );
    }
    if (step === 1) {
      return saveSection(
        {
          primary_borrower: borrowerPayload(primary, false),
          co_borrower: coBorrower ? borrowerPayload(coBorrower, true) : null,
        },
        sectionIssues(1),
      );
    }
    if (step === 2) {
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
        sectionIssues(2),
      );
    }
    if (step === 3) {
      return saveSection(
        {
          assets: assets.map((asset) =>
            compact({
              asset_type: asset.asset_type,
              value: numberValue(asset.value),
              description: asset.description || undefined,
            }),
          ),
          assets_complete: assetsComplete,
          liabilities: liabilities.map((liability) =>
            compact({
              liability_type: liability.liability_type,
              current_balance: numberValue(liability.current_balance),
              payment_amount: numberValue(liability.payment_amount),
              payment_frequency: liability.payment_frequency || undefined,
              description: liability.description || undefined,
            }),
          ),
          liabilities_complete: liabilitiesComplete,
        },
        sectionIssues(3),
      );
    }
    if (step === 4) {
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
                year_built: numberValue(subjectProperty.year_built, "integer"),
                livable_area_sqft: numberValue(
                  subjectProperty.livable_area_sqft,
                  "integer",
                ),
                units: numberValue(subjectProperty.units, "integer"),
                monthly_property_tax: numberValue(
                  subjectProperty.monthly_property_tax,
                ),
                monthly_heating_cost: numberValue(
                  subjectProperty.monthly_heating_cost,
                ),
                monthly_condo_fee: numberValue(
                  subjectProperty.monthly_condo_fee,
                ),
                lot_details: subjectProperty.lot_details || undefined,
                garage_details: subjectProperty.garage_details || undefined,
              })
            : null,
        },
        sectionIssues(4),
      );
    }
    if (step === 5) {
      return saveSection(
        {
          other_properties: otherProperties.map((property) => ({
            address: property.address || undefined,
            purchase_date: property.purchase_date || undefined,
            purchase_price: numberValue(property.purchase_price),
            estimated_value: numberValue(property.estimated_value),
            is_owner_occupied: property.is_owner_occupied,
            mortgages: property.mortgages.map((mortgage) =>
              compact({
                balance: numberValue(mortgage.balance),
                payment_amount: numberValue(mortgage.payment_amount),
                payment_frequency: mortgage.payment_frequency,
                maturity_date: mortgage.maturity_date || undefined,
              }),
            ),
          })),
        },
        sectionIssues(5),
      );
    }
    if (step === 6) {
      return saveSection({ additional_notes: notes || null });
    }
  }

  async function submitApplication() {
    if (!draft || !consent || !consentAcknowledged || !documentsSettled) return;
    const incomplete = incompleteSections();
    if (incomplete.length) {
      const summary = incomplete.flatMap(({ index, issues }) => [
        ...issues
          .slice(0, 3)
          .map((issue) => `${steps[index]} — ${issue.label}: ${issue.message}`),
        ...(issues.length > 3
          ? [
              `${steps[index]} — and ${issues.length - 3} more to fix in this section.`,
            ]
          : []),
      ]);
      const allIssues = incomplete.flatMap(({ issues }) => issues);
      setErrorTitle("Finish these sections before submitting");
      setFieldErrors(fieldMessages(allIssues));
      setErrors(summary);
      setStep(incomplete[0].index);
      focusField(allIssues[0]?.field);
      return;
    }
    setErrors([]);
    setFieldErrors({});
    setSubmitting(true);
    try {
      await (api.submit ?? submitBorrowerApplication)(
        draft.application_id,
        draft.revision,
        consent,
        coBorrower || hasSavedCoBorrower ? "both" : "primary",
      );
      forgetBorrowerApplicationId();
      setSubmitted(true);
    } catch (error) {
      const failure = saveFailure(error);
      setErrors(failure.summary);
      setFieldErrors(fieldErrorsFor(failure.issues, issueState()));
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="container borrower-page">
        <section role="status" className="success-state">
          <h1>Application submitted</h1>
          <p>
            Keeper confirmed durable submission. This browser no longer retains
            the application locator and cannot reopen the submitted record.
          </p>
        </section>
      </div>
    );
  }

  return (
    <div className="container borrower-page">
      <header className="borrower-intro">
        <h1>Mortgage application</h1>
        {recovered ? (
          restoredData ? (
            <p
              className="borrower-inline-status save-feedback-saved"
              role="status"
            >
              Existing private draft recovered. Saved non-SIN answers have been
              restored; SIN remains provided/masked only.
            </p>
          ) : (
            <p className="borrower-inline-status" role="status">
              Saved draft found. No previous answers were restored yet; continue
              where you left off.
            </p>
          )
        ) : null}
      </header>
      <AgentPreferenceSection
        attributedAgentName={attributedAgentName}
        value={mortgage.preferred_agent_name}
        onChange={(next) =>
          setMortgage((current) => ({ ...current, preferred_agent_name: next }))
        }
      />
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
          <h2 id="borrower-error-heading">{errorTitle}</h2>
          <ul>
            {errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        </section>
      ) : null}
      <section aria-labelledby="borrower-step-heading">
        <h2
          className="visually-hidden"
          id="borrower-step-heading"
          tabIndex={-1}
        >
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
              disabled={
                saveState === "saving" || (step === 7 && !documentsSettled)
              }
              onClick={() =>
                step === 7
                  ? setStep((current) => current + 1)
                  : void currentSave()
              }
            >
              {step === 7
                ? "Continue to consent"
                : saveState === "saving"
                  ? "Saving…"
                  : "Save and continue"}
            </Button>
          ) : (
            <Button
              type="button"
              disabled={
                submitting ||
                !consent ||
                !consentAcknowledged ||
                !documentsSettled
              }
              onClick={() => void submitApplication()}
            >
              {submitting ? "Submitting…" : "Submit application"}
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
              ? savedAt
                ? `Section saved securely — ${formatRelativeTime(savedAt, now)}.`
                : "Section saved securely."
              : saveState === "error"
                ? "Nothing was advanced or cleared."
                : ""}
        </p>
      </div>
      <p className="borrower-privacy-note">
        Your draft is saved section by section in Keeper&apos;s encrypted server
        state, not in browser storage, URLs, analytics, or server-rendered
        markup. Use a private device; this browser needs its secure capability
        cookie to resume the draft.
      </p>
    </div>
  );
}
