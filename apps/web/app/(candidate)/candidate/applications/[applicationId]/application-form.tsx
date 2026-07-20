"use client";

import { useEffect, useRef, useState } from "react";
import { Button, ConfirmationDialog, FormField, StatusBadge } from "@keeper/ui";
import {
  CandidateRequestError,
  candidateBrowserJson,
  type CandidateValidationIssue,
} from "@/lib/candidate-browser-api";
import type {
  CandidateApplication,
  CandidatePrivacyDisclosure,
} from "@/lib/recruitment-api";

type Employment = CandidateApplication["employment"][number];
type Education = CandidateApplication["education"][number];
type FormIssue = { fieldId: string | null; message: string };
type SaveStatus =
  | "idle"
  | "saving"
  | "saved"
  | "validation_error"
  | "network_error"
  | "conflict";
const sensitiveWarning =
  "Do not include identification numbers, financial or health information, passwords, background-check information, licence numbers, or anything not requested.";
const monthPattern = /^(19|20)\d{2}-(0[1-9]|1[0-2])$/;
const datePattern = /^\d{4}-(0[1-9]|1[0-2])-([0-2]\d|3[01])$/;
const referralDetailSources = new Set(["employee_or_agent_referral", "other"]);

function value(form: FormData, name: string): string | null {
  const result = String(form.get(name) ?? "").trim();
  return result || null;
}

function clientValidationIssues(
  form: FormData,
  employment: Employment[],
  education: Education[],
  requireSubmissionFields: boolean,
): FormIssue[] {
  const issues: FormIssue[] = [];
  if (requireSubmissionFields) {
    const checks: Array<[string, string]> = [
      ["given_name", "First/given name"],
      ["family_name", "Last/family name"],
      ["phone", "Phone number"],
      ["city", "City"],
      ["country_code", "Country"],
      ["preferred_contact_method", "Preferred contact method"],
    ];
    for (const [fieldId, label] of checks) {
      if (!value(form, fieldId)) {
        issues.push({ fieldId, message: `${label} is required.` });
      }
    }
  }
  const phone = value(form, "phone");
  if (phone) {
    const digits = phone.replace(/\D/g, "");
    if (
      !phone.startsWith("+") ||
      !/^\+?[0-9 ().-]+$/.test(phone) ||
      digits.length < 8 ||
      digits.length > 15
    ) {
      issues.push({
        fieldId: "phone",
        message:
          "Phone number must start with + and contain 8 to 15 digits, including the country code.",
      });
    }
  }
  const country = value(form, "country_code");
  if (country && !/^[A-Za-z]{2}$/.test(country)) {
    issues.push({
      fieldId: "country_code",
      message:
        "Country must be a valid two-letter ISO country code, such as CA.",
    });
  }
  const available = value(form, "available_from");
  if (available && !datePattern.test(available)) {
    issues.push({
      fieldId: "available_from",
      message: "Earliest available date must use YYYY-MM-DD.",
    });
  }
  const interest = value(form, "interest_statement") ?? "";
  if (requireSubmissionFields && interest.length < 100) {
    issues.push({
      fieldId: "interest_statement",
      message: "Interest statement must contain at least 100 characters.",
    });
  }
  employment.forEach((entry, index) => {
    if (!entry.employer_name.trim()) {
      issues.push({
        fieldId: `employer-${index}`,
        message: `Employment entry ${index + 1}: employer is required.`,
      });
    }
    if (!entry.role_title.trim()) {
      issues.push({
        fieldId: `role-${index}`,
        message: `Employment entry ${index + 1}: role/title is required.`,
      });
    }
    if (!monthPattern.test(entry.start_month)) {
      issues.push({
        fieldId: `start-${index}`,
        message: `Employment entry ${index + 1}: start month must use YYYY-MM.`,
      });
    }
    if (entry.currently_employed && entry.end_month) {
      issues.push({
        fieldId: `employment-current-${index}`,
        message: `Employment entry ${index + 1}: remove the end month for current employment.`,
      });
    }
    if (!entry.currently_employed) {
      if (!entry.end_month || !monthPattern.test(entry.end_month)) {
        issues.push({
          fieldId: `end-${index}`,
          message: `Employment entry ${index + 1}: end month must use YYYY-MM.`,
        });
      } else if (
        monthPattern.test(entry.start_month) &&
        entry.end_month < entry.start_month
      ) {
        issues.push({
          fieldId: `end-${index}`,
          message: `Employment entry ${index + 1}: end month cannot be before start month.`,
        });
      }
    }
  });
  education.forEach((entry, index) => {
    if (!entry.institution_name.trim()) {
      issues.push({
        fieldId: `institution-${index}`,
        message: `Education entry ${index + 1}: institution/provider is required.`,
      });
    }
    if (!entry.program_name.trim()) {
      issues.push({
        fieldId: `program-${index}`,
        message: `Education entry ${index + 1}: program/course is required.`,
      });
    }
    if (
      entry.completion_year != null &&
      (entry.completion_year < 1900 ||
        entry.completion_year > new Date().getFullYear())
    ) {
      issues.push({
        fieldId: `completion-${index}`,
        message: `Education entry ${index + 1}: completion year must be between 1900 and the current year.`,
      });
    }
  });
  if (requireSubmissionFields && form.get("privacy_acknowledged") !== "on") {
    issues.push({
      fieldId: "privacy_acknowledged",
      message: "You must acknowledge the candidate privacy disclosure.",
    });
  }
  if (
    requireSubmissionFields &&
    form.get("information_accuracy_confirmed") !== "on"
  ) {
    issues.push({
      fieldId: "information_accuracy_confirmed",
      message: "You must confirm the information is accurate.",
    });
  }
  return issues;
}

function serverIssue(issue: CandidateValidationIssue): FormIssue {
  if (issue.message.toLowerCase().includes("referral detail")) {
    return {
      fieldId: "referral_detail",
      message:
        "Referral details are allowed only for an employee/agent referral or Other.",
    };
  }
  const path = issue.path.filter((part) => part !== "body");
  const top = typeof path[0] === "string" ? path[0] : null;
  const index = typeof path[1] === "number" ? path[1] : null;
  const nested = typeof path[2] === "string" ? path[2] : null;
  if (top === "employment" && index !== null) {
    const ids: Record<string, string> = {
      employer_name: `employer-${index}`,
      role_title: `role-${index}`,
      start_month: `start-${index}`,
      end_month: `end-${index}`,
      summary: `employment-summary-${index}`,
    };
    const labels: Record<string, string> = {
      employer_name: "employer/organization",
      role_title: "role/title",
      start_month: "start month in YYYY-MM format",
      end_month: "eligible end month in YYYY-MM format",
      summary: "responsibilities/highlights",
    };
    return {
      fieldId: nested ? (ids[nested] ?? `start-${index}`) : `start-${index}`,
      message: `Employment entry ${index + 1} requires a valid ${nested ? (labels[nested] ?? "value") : "month range and current-employment selection"}.`,
    };
  }
  if (top === "education" && index !== null) {
    const ids: Record<string, string> = {
      institution_name: `institution-${index}`,
      program_name: `program-${index}`,
      completion_year: `completion-${index}`,
    };
    return {
      fieldId: nested
        ? (ids[nested] ?? `institution-${index}`)
        : `institution-${index}`,
      message: `Education entry ${index + 1} contains an invalid ${nested?.replaceAll("_", " ") ?? "value"}.`,
    };
  }
  const messages: Record<string, string> = {
    given_name: "First/given name must contain 1 to 70 plain-text characters.",
    family_name: "Last/family name must contain 1 to 70 plain-text characters.",
    preferred_name: "Preferred name must not exceed 70 plain-text characters.",
    phone:
      "Phone number must start with + and contain 8 to 15 digits, including the country code.",
    city: "City must contain 1 to 100 plain-text characters.",
    region: "Province/state/region must not exceed 100 plain-text characters.",
    country_code:
      "Country must be a valid two-letter ISO country code, such as CA.",
    preferred_contact_method: "Select an available preferred contact method.",
    available_from: "Earliest available date must use YYYY-MM-DD.",
    referral_source: "Select an available referral source.",
    referral_detail:
      "Referral details are allowed only for an employee/agent referral or Other.",
    interest_statement:
      "Interest statement must contain 100 to 2,000 plain-text characters before submission.",
    relevant_experience:
      "Relevant experience must not exceed 2,000 plain-text characters.",
  };
  return {
    fieldId: top && messages[top] ? top : null,
    message:
      (top && messages[top]) ||
      "One application value is not in the accepted format. Review the visible field guidance.",
  };
}

function requestIssues(error: unknown): FormIssue[] {
  if (!(error instanceof CandidateRequestError)) return [];
  if (error.issues.length) return error.issues.map(serverIssue);
  if (error.detail?.includes("referral detail")) {
    return [
      {
        fieldId: "referral_detail",
        message:
          "Referral details are allowed only for an employee/agent referral or Other.",
      },
    ];
  }
  return [];
}

export function CandidateApplicationForm({
  initialApplication,
  disclosure,
  requestJson = (path, init) =>
    candidateBrowserJson<CandidateApplication>(path, init),
}: {
  initialApplication: CandidateApplication;
  disclosure: CandidatePrivacyDisclosure;
  requestJson?: (
    path: string,
    init?: RequestInit,
  ) => Promise<CandidateApplication>;
}) {
  const [application, setApplication] = useState(initialApplication);
  const [employment, setEmployment] = useState<Employment[]>(
    initialApplication.employment,
  );
  const [education, setEducation] = useState<Education[]>(
    initialApplication.education,
  );
  const [referralSource, setReferralSource] = useState(
    initialApplication.referral_source ?? "",
  );
  const [referralDetail, setReferralDetail] = useState(
    initialApplication.referral_detail ?? "",
  );
  const [interestStatement, setInterestStatement] = useState(
    initialApplication.interest_statement ?? "",
  );
  const [relevantExperience, setRelevantExperience] = useState(
    initialApplication.relevant_experience ?? "",
  );
  const [errors, setErrors] = useState<FormIssue[]>([]);
  const [notice, setNotice] = useState("");
  const [saveStatus, setSaveStatus] = useState<SaveStatus>("idle");
  const [saveMessage, setSaveMessage] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const saveButtonRef = useRef<HTMLButtonElement>(null);
  const restoreSaveFocusRef = useRef(false);
  const withdrawButtonRef = useRef<HTMLButtonElement>(null);
  const noticeRef = useRef<HTMLParagraphElement>(null);
  const errorSummaryRef = useRef<HTMLElement>(null);
  const focusErrorSummaryRef = useRef(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const editable = application.state === "draft";
  const fieldError = (fieldId: string) =>
    errors.find((error) => error.fieldId === fieldId)?.message;
  const referralDetailAllowed = referralDetailSources.has(referralSource);

  useEffect(() => {
    if (errors.length && focusErrorSummaryRef.current) {
      errorSummaryRef.current?.focus();
      focusErrorSummaryRef.current = false;
    }
  }, [errors]);

  useEffect(() => {
    if (!busy && restoreSaveFocusRef.current) {
      saveButtonRef.current?.focus();
      restoreSaveFocusRef.current = false;
    }
  }, [busy]);

  function showRequestError(
    error: unknown,
    fallback: string,
    { focusSummary = true }: { focusSummary?: boolean } = {},
  ) {
    focusErrorSummaryRef.current = focusSummary;
    const mapped = requestIssues(error);
    if (mapped.length) {
      setErrors(mapped);
    } else if (error instanceof CandidateRequestError && error.status === 409) {
      setErrors([
        {
          fieldId: null,
          message:
            "This application changed in another request. Refresh the page before saving again.",
        },
      ]);
    } else {
      setErrors([{ fieldId: null, message: fallback }]);
    }
    setNotice("");
  }

  function draftPayload(form: FormData) {
    return {
      expected_revision: application.revision,
      given_name: value(form, "given_name"),
      family_name: value(form, "family_name"),
      preferred_name: value(form, "preferred_name"),
      phone: value(form, "phone"),
      city: value(form, "city"),
      region: value(form, "region"),
      country_code: value(form, "country_code"),
      preferred_contact_method: value(form, "preferred_contact_method"),
      available_from: value(form, "available_from"),
      referral_source: referralSource || null,
      referral_detail:
        referralDetailAllowed && referralDetail.trim()
          ? referralDetail.trim()
          : null,
      interest_statement: interestStatement.trim() || null,
      relevant_experience: relevantExperience.trim() || null,
      employment,
      education,
      privacy_acknowledged: form.get("privacy_acknowledged") === "on",
      information_accuracy_confirmed:
        form.get("information_accuracy_confirmed") === "on",
    };
  }

  async function saveDraft() {
    if (!formRef.current || busy) return;
    const form = new FormData(formRef.current);
    const nextErrors = clientValidationIssues(
      form,
      employment,
      education,
      false,
    );
    setErrors(nextErrors);
    if (nextErrors.length) {
      setNotice("");
      setSaveStatus("validation_error");
      setSaveMessage("Draft not saved. Review the highlighted fields.");
      return;
    }
    restoreSaveFocusRef.current =
      document.activeElement === saveButtonRef.current;
    setBusy(true);
    setErrors([]);
    setNotice("Saving draft…");
    setSaveStatus("saving");
    setSaveMessage("Saving draft…");
    try {
      const updated = await requestJson(
        `/api/v1/candidate/applications/${application.id}`,
        {
          method: "PATCH",
          body: JSON.stringify(draftPayload(form)),
        },
      );
      setApplication(updated);
      setNotice("Draft saved.");
      setSaveStatus("saved");
      setSaveMessage("Draft saved.");
    } catch (error) {
      showRequestError(
        error,
        "The draft could not be saved. Your current page has not been submitted.",
        { focusSummary: false },
      );
      if (error instanceof CandidateRequestError && error.status === 409) {
        setSaveStatus("conflict");
        setSaveMessage(
          "Draft not saved because this application changed elsewhere. Refresh before trying again.",
        );
      } else if (requestIssues(error).length) {
        setSaveStatus("validation_error");
        setSaveMessage("Draft not saved. Review the highlighted fields.");
      } else {
        setSaveStatus("network_error");
        setSaveMessage("Draft not saved. Check your connection and try again.");
      }
    } finally {
      setBusy(false);
    }
  }

  async function review(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = new FormData(event.currentTarget);
    const nextErrors = clientValidationIssues(
      form,
      employment,
      education,
      true,
    );
    focusErrorSummaryRef.current = nextErrors.length > 0;
    setErrors(nextErrors);
    if (nextErrors.length !== 0) return;
    setBusy(true);
    setNotice("Saving draft for review…");
    try {
      const updated = await requestJson(
        `/api/v1/candidate/applications/${application.id}`,
        { method: "PATCH", body: JSON.stringify(draftPayload(form)) },
      );
      setApplication(updated);
      setNotice("Draft saved. Review the information before submission.");
      setReviewing(true);
    } catch (error) {
      showRequestError(
        error,
        "The draft could not be saved for review. The application has not been submitted.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function submitApplication() {
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Submitting application…");
    try {
      const updated = await requestJson(
        `/api/v1/candidate/applications/${application.id}/submit`,
        {
          method: "POST",
          body: JSON.stringify({ expected_revision: application.revision }),
        },
      );
      setApplication(updated);
      setReviewing(false);
      setNotice("Application submitted. Your questionnaire is now read-only.");
    } catch (error) {
      showRequestError(
        error,
        "The application was not submitted. Save the draft and review any changed fields.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function withdraw() {
    if (busy) return;
    setBusy(true);
    try {
      const updated = await requestJson(
        `/api/v1/candidate/applications/${application.id}/withdraw`,
        {
          method: "POST",
          body: JSON.stringify({ expected_revision: application.revision }),
        },
      );
      setApplication(updated);
      setNotice("Application withdrawn. The retained record is read-only.");
      setWithdrawOpen(false);
      // Return focus to the persistent status region so keyboard and
      // screen-reader users are not stranded after the modal closes and the
      // withdraw trigger is unmounted.
      noticeRef.current?.focus();
    } catch {
      setErrors([
        { fieldId: null, message: "The application could not be withdrawn." },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function cancelWithdrawal() {
    setWithdrawOpen(false);
    withdrawButtonRef.current?.focus();
  }

  return (
    <div className="application-workflow">
      <div
        className="progress-nav"
        aria-labelledby="application-sections-title"
      >
        <p id="application-sections-title" className="progress-nav-title">
          Application sections
        </p>
        <ol>
          <li>Opportunity</li>
          <li>Contact information</li>
          <li>Application details</li>
          <li>Optional history</li>
          <li>Privacy and review</li>
        </ol>
      </div>
      <p>
        Current status:{" "}
        <StatusBadge>{application.status.replaceAll("_", " ")}</StatusBadge>
      </p>
      <p aria-live="polite" role="status" tabIndex={-1} ref={noticeRef}>
        {notice}
      </p>
      {errors.length ? (
        <section
          ref={errorSummaryRef}
          className="error-summary"
          role="alert"
          aria-labelledby="application-error-summary-title"
          tabIndex={-1}
        >
          <h2 id="application-error-summary-title">Please check the form</h2>
          <ul>
            {errors.map((error, index) => (
              <li key={`${error.fieldId ?? "form"}-${index}`}>
                {error.fieldId ? (
                  <a
                    href={`#${error.fieldId}`}
                    onClick={(event) => {
                      event.preventDefault();
                      document.getElementById(error.fieldId ?? "")?.focus();
                    }}
                  >
                    {error.message}
                  </a>
                ) : (
                  error.message
                )}
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {reviewing ? (
        <section className="card" aria-labelledby="review-heading">
          <h2 id="review-heading">Review before submission</h2>
          <p>
            Review the saved information for {application.source_posting_title}.
            Submission freezes the questionnaire. Optional documents can still
            be added while the application remains active.
          </p>
          <dl>
            <dt>Candidate</dt>
            <dd>
              {application.given_name} {application.family_name}
            </dd>
            <dt>Verified email</dt>
            <dd>{application.email}</dd>
            <dt>Disclosure version</dt>
            <dd>{disclosure.version}</dd>
          </dl>
          <div className="button-row">
            <Button
              type="button"
              onClick={() => setReviewing(false)}
              disabled={busy}
            >
              Return to edit
            </Button>
            <Button type="button" onClick={submitApplication} disabled={busy}>
              Submit application
            </Button>
          </div>
        </section>
      ) : (
        <form ref={formRef} onSubmit={review} aria-busy={busy} noValidate>
          <fieldset disabled={!editable || busy}>
            <legend>Opportunity</legend>
            <p>
              <strong>{application.source_posting_title}</strong>
            </p>
            <p>Posting source version {application.source_posting_version}</p>
          </fieldset>
          <fieldset disabled={!editable || busy}>
            <legend>Contact information</legend>
            <div className="grid-2">
              <FormField
                id="given_name"
                label="First/given name (required)"
                hint="1 to 70 plain-text characters."
                error={fieldError("given_name")}
              >
                <input
                  id="given_name"
                  name="given_name"
                  defaultValue={application.given_name ?? ""}
                  maxLength={70}
                  required
                />
              </FormField>
              <FormField
                id="family_name"
                label="Last/family name (required)"
                hint="1 to 70 plain-text characters."
                error={fieldError("family_name")}
              >
                <input
                  id="family_name"
                  name="family_name"
                  defaultValue={application.family_name ?? ""}
                  maxLength={70}
                  required
                />
              </FormField>
              <FormField
                id="preferred_name"
                label="Preferred name (optional)"
                hint="Up to 70 plain-text characters."
                error={fieldError("preferred_name")}
              >
                <input
                  id="preferred_name"
                  name="preferred_name"
                  defaultValue={application.preferred_name ?? ""}
                  maxLength={70}
                />
              </FormField>
              <FormField
                id="email"
                label="Verified email (required account value)"
              >
                <input id="email" value={application.email} readOnly />
              </FormField>
              <FormField
                id="phone"
                label="Phone number (required)"
                hint="Start with + and include the country code; 8 to 15 digits after normalization. Example: +1 416 555 0100."
                error={fieldError("phone")}
              >
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  defaultValue={application.phone ?? ""}
                  maxLength={32}
                  pattern="\+[0-9 ().-]{8,31}"
                  required
                />
              </FormField>
              <FormField
                id="city"
                label="City (required)"
                hint="1 to 100 plain-text characters."
                error={fieldError("city")}
              >
                <input
                  id="city"
                  name="city"
                  defaultValue={application.city ?? ""}
                  maxLength={100}
                  required
                />
              </FormField>
              <FormField
                id="region"
                label="Province/state/region (optional)"
                hint="Up to 100 plain-text characters."
                error={fieldError("region")}
              >
                <input
                  id="region"
                  name="region"
                  defaultValue={application.region ?? ""}
                  maxLength={100}
                />
              </FormField>
              <FormField
                id="country_code"
                label="Country (required)"
                hint="Two-letter ISO 3166-1 country code, such as CA."
                error={fieldError("country_code")}
              >
                <input
                  id="country_code"
                  name="country_code"
                  defaultValue={application.country_code ?? "CA"}
                  minLength={2}
                  maxLength={2}
                  pattern="[A-Za-z]{2}"
                  autoCapitalize="characters"
                  required
                />
              </FormField>
              <FormField
                id="preferred_contact_method"
                label="Preferred contact method (required)"
                error={fieldError("preferred_contact_method")}
              >
                <select
                  id="preferred_contact_method"
                  name="preferred_contact_method"
                  defaultValue={application.preferred_contact_method ?? ""}
                  required
                >
                  <option value="">Select one</option>
                  <option value="email">Email</option>
                  <option value="phone">Phone</option>
                  <option value="no_preference">No preference</option>
                </select>
              </FormField>
            </div>
          </fieldset>
          <fieldset disabled={!editable || busy}>
            <legend>Application details</legend>
            <FormField
              id="available_from"
              label="Earliest available start date (optional)"
              hint="Choose a date or enter it as YYYY-MM-DD, for example 2026-09-01."
              error={fieldError("available_from")}
            >
              <input
                id="available_from"
                name="available_from"
                type="date"
                defaultValue={application.available_from ?? ""}
              />
            </FormField>
            <FormField
              id="referral_source"
              label="How did you hear about this opportunity? (optional)"
              hint="Referral details are requested only for an employee/agent referral or Other."
              error={fieldError("referral_source")}
            >
              <select
                id="referral_source"
                name="referral_source"
                value={referralSource}
                onChange={(event) => {
                  const nextSource = event.target.value;
                  setReferralSource(nextSource);
                  if (!referralDetailSources.has(nextSource)) {
                    setReferralDetail("");
                  }
                }}
              >
                <option value="">Prefer not to answer</option>
                <option value="keeper_website">Keeper website</option>
                <option value="search">Search</option>
                <option value="social_media">Social media</option>
                <option value="employee_or_agent_referral">
                  Employee or agent referral
                </option>
                <option value="event">Event</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
            </FormField>
            {referralDetailAllowed ? (
              <FormField
                id="referral_detail"
                label="Referral details (optional)"
                hint="Up to 120 plain-text characters. Leave blank if you prefer not to identify the person or source."
                error={fieldError("referral_detail")}
              >
                <input
                  id="referral_detail"
                  name="referral_detail"
                  value={referralDetail}
                  maxLength={120}
                  onChange={(event) => setReferralDetail(event.target.value)}
                />
              </FormField>
            ) : (
              <p className="notice">
                Referral details are not collected for the selected source.
              </p>
            )}
            <FormField
              id="interest_statement"
              label="Why are you interested in this opportunity? (required)"
              hint={`100 to 2,000 characters are required before submission. ${sensitiveWarning}`}
              error={fieldError("interest_statement")}
            >
              <textarea
                id="interest_statement"
                name="interest_statement"
                value={interestStatement}
                minLength={100}
                maxLength={2000}
                required
                onChange={(event) => setInterestStatement(event.target.value)}
              />
            </FormField>
            <p id="interest-statement-count" role="status" aria-live="polite">
              {interestStatement.length} of 2,000 characters; minimum 100 for
              submission.
            </p>
            <FormField
              id="relevant_experience"
              label="Relevant experience (optional)"
              hint={`Up to 2,000 characters. ${sensitiveWarning}`}
              error={fieldError("relevant_experience")}
            >
              <textarea
                id="relevant_experience"
                name="relevant_experience"
                value={relevantExperience}
                maxLength={2000}
                onChange={(event) => setRelevantExperience(event.target.value)}
              />
            </FormField>
            <p role="status" aria-live="polite">
              {relevantExperience.length} of 2,000 characters.
            </p>
          </fieldset>
          <fieldset disabled={!editable || busy}>
            <legend>Employment history (optional)</legend>
            {employment.map((entry, index) => (
              <section
                className="card repeat-entry"
                key={index}
                aria-label={`Employment entry ${index + 1}`}
              >
                <FormField
                  id={`employer-${index}`}
                  label="Employer/organization (required for this entry)"
                  hint="1 to 160 plain-text characters."
                  error={fieldError(`employer-${index}`)}
                >
                  <input
                    id={`employer-${index}`}
                    name={`employment-${index}-employer`}
                    value={entry.employer_name}
                    maxLength={160}
                    required
                    onChange={(event) =>
                      setEmployment((items) =>
                        items.map((item, position) =>
                          position === index
                            ? { ...item, employer_name: event.target.value }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
                <FormField
                  id={`role-${index}`}
                  label="Role/title (required for this entry)"
                  hint="1 to 160 plain-text characters."
                  error={fieldError(`role-${index}`)}
                >
                  <input
                    id={`role-${index}`}
                    name={`employment-${index}-role`}
                    value={entry.role_title}
                    maxLength={160}
                    required
                    onChange={(event) =>
                      setEmployment((items) =>
                        items.map((item, position) =>
                          position === index
                            ? { ...item, role_title: event.target.value }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
                <FormField
                  id={`start-${index}`}
                  label="Start month (required for this entry)"
                  hint="Choose a month or enter YYYY-MM, for example 2024-01."
                  error={fieldError(`start-${index}`)}
                >
                  <input
                    id={`start-${index}`}
                    name={`employment-${index}-start-month`}
                    type="month"
                    pattern="(19|20)[0-9]{2}-(0[1-9]|1[0-2])"
                    placeholder="YYYY-MM"
                    value={entry.start_month}
                    required
                    onChange={(event) =>
                      setEmployment((items) =>
                        items.map((item, position) =>
                          position === index
                            ? { ...item, start_month: event.target.value }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
                <label
                  className="consent"
                  htmlFor={`employment-current-${index}`}
                >
                  <input
                    id={`employment-current-${index}`}
                    name={`employment-${index}-current`}
                    type="checkbox"
                    checked={entry.currently_employed}
                    onChange={(event) =>
                      setEmployment((items) =>
                        items.map((item, position) =>
                          position === index
                            ? {
                                ...item,
                                currently_employed: event.target.checked,
                                end_month: event.target.checked
                                  ? null
                                  : item.end_month,
                              }
                            : item,
                        ),
                      )
                    }
                  />
                  I currently work here
                </label>
                {!entry.currently_employed ? (
                  <FormField
                    id={`end-${index}`}
                    label="End month (required for past roles)"
                    hint="Choose a month or enter YYYY-MM. It cannot be before the start month."
                    error={fieldError(`end-${index}`)}
                  >
                    <input
                      id={`end-${index}`}
                      name={`employment-${index}-end-month`}
                      type="month"
                      pattern="(19|20)[0-9]{2}-(0[1-9]|1[0-2])"
                      placeholder="YYYY-MM"
                      value={entry.end_month ?? ""}
                      required
                      onChange={(event) =>
                        setEmployment((items) =>
                          items.map((item, position) =>
                            position === index
                              ? { ...item, end_month: event.target.value }
                              : item,
                          ),
                        )
                      }
                    />
                  </FormField>
                ) : null}
                <FormField
                  id={`employment-summary-${index}`}
                  label="Responsibilities or highlights (optional)"
                  hint={`Up to 1,000 characters. ${sensitiveWarning}`}
                  error={fieldError(`employment-summary-${index}`)}
                >
                  <textarea
                    id={`employment-summary-${index}`}
                    name={`employment-${index}-summary`}
                    value={entry.summary ?? ""}
                    maxLength={1000}
                    onChange={(event) =>
                      setEmployment((items) =>
                        items.map((item, position) =>
                          position === index
                            ? { ...item, summary: event.target.value || null }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
                <Button
                  type="button"
                  onClick={() =>
                    setEmployment((items) =>
                      items.filter((_, position) => position !== index),
                    )
                  }
                >
                  Remove employment entry
                </Button>
              </section>
            ))}
            {employment.length < 5 ? (
              <Button
                type="button"
                onClick={() =>
                  setEmployment((items) => [
                    ...items,
                    {
                      employer_name: "",
                      role_title: "",
                      start_month: "",
                      currently_employed: false,
                      end_month: "",
                      summary: null,
                    },
                  ])
                }
              >
                Add employment entry
              </Button>
            ) : null}
          </fieldset>
          <fieldset disabled={!editable || busy}>
            <legend>Education and training (optional)</legend>
            {education.map((entry, index) => (
              <section
                className="card repeat-entry"
                key={index}
                aria-label={`Education entry ${index + 1}`}
              >
                <FormField
                  id={`institution-${index}`}
                  label="Institution/provider (required for this entry)"
                  hint="1 to 160 plain-text characters."
                  error={fieldError(`institution-${index}`)}
                >
                  <input
                    id={`institution-${index}`}
                    name={`education-${index}-institution`}
                    value={entry.institution_name}
                    maxLength={160}
                    required
                    onChange={(event) =>
                      setEducation((items) =>
                        items.map((item, position) =>
                          position === index
                            ? { ...item, institution_name: event.target.value }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
                <FormField
                  id={`program-${index}`}
                  label="Program/course (required for this entry)"
                  hint="1 to 160 plain-text characters."
                  error={fieldError(`program-${index}`)}
                >
                  <input
                    id={`program-${index}`}
                    name={`education-${index}-program`}
                    value={entry.program_name}
                    maxLength={160}
                    required
                    onChange={(event) =>
                      setEducation((items) =>
                        items.map((item, position) =>
                          position === index
                            ? { ...item, program_name: event.target.value }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
                <FormField
                  id={`completion-${index}`}
                  label="Completion year (optional)"
                  hint={`Four digits from 1900 through ${new Date().getFullYear()}.`}
                  error={fieldError(`completion-${index}`)}
                >
                  <input
                    id={`completion-${index}`}
                    name={`education-${index}-completion-year`}
                    type="number"
                    min={1900}
                    max={new Date().getFullYear()}
                    value={entry.completion_year ?? ""}
                    onChange={(event) =>
                      setEducation((items) =>
                        items.map((item, position) =>
                          position === index
                            ? {
                                ...item,
                                completion_year: event.target.value
                                  ? Number(event.target.value)
                                  : null,
                              }
                            : item,
                        ),
                      )
                    }
                  />
                </FormField>
                <Button
                  type="button"
                  onClick={() =>
                    setEducation((items) =>
                      items.filter((_, position) => position !== index),
                    )
                  }
                >
                  Remove education entry
                </Button>
              </section>
            ))}
            {education.length < 3 ? (
              <Button
                type="button"
                onClick={() =>
                  setEducation((items) => [
                    ...items,
                    {
                      institution_name: "",
                      program_name: "",
                      completion_year: null,
                    },
                  ])
                }
              >
                Add education entry
              </Button>
            ) : null}
          </fieldset>
          <fieldset disabled={!editable || busy}>
            <legend>Privacy and declaration</legend>
            <section
              className="privacy-disclosure"
              aria-labelledby="candidate-disclosure-title"
            >
              <h2 id="candidate-disclosure-title">{disclosure.title}</h2>
              {disclosure.paragraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
              <p>
                <strong>Version:</strong> {disclosure.version}
              </p>
            </section>
            <label className="consent">
              <input
                id="privacy_acknowledged"
                name="privacy_acknowledged"
                type="checkbox"
                defaultChecked={application.privacy_acknowledged}
                aria-describedby={
                  fieldError("privacy_acknowledged")
                    ? "privacy-acknowledged-error"
                    : undefined
                }
                aria-invalid={
                  fieldError("privacy_acknowledged") ? true : undefined
                }
              />
              I have read the candidate privacy disclosure (required for
              submission)
            </label>
            {fieldError("privacy_acknowledged") ? (
              <p id="privacy-acknowledged-error" className="field-error">
                {fieldError("privacy_acknowledged")}
              </p>
            ) : null}
            <label className="consent">
              <input
                id="information_accuracy_confirmed"
                name="information_accuracy_confirmed"
                type="checkbox"
                defaultChecked={application.information_accuracy_confirmed}
                aria-describedby={
                  fieldError("information_accuracy_confirmed")
                    ? "accuracy-confirmed-error"
                    : undefined
                }
                aria-invalid={
                  fieldError("information_accuracy_confirmed")
                    ? true
                    : undefined
                }
              />
              I confirm that the information I am submitting is accurate to the
              best of my knowledge (required for submission)
            </label>
            {fieldError("information_accuracy_confirmed") ? (
              <p id="accuracy-confirmed-error" className="field-error">
                {fieldError("information_accuracy_confirmed")}
              </p>
            ) : null}
            <p>
              This accuracy confirmation is not an electronic signature,
              licensing attestation, background consent, identity verification,
              or suitability declaration.
            </p>
          </fieldset>
          {editable ? (
            <div className="application-actions">
              <div className="button-row">
                <Button
                  ref={saveButtonRef}
                  type="button"
                  onClick={saveDraft}
                  disabled={busy}
                >
                  {saveStatus === "saving"
                    ? "Saving…"
                    : saveStatus === "saved"
                      ? "Saved"
                      : "Save draft"}
                </Button>
                <Button type="submit" disabled={busy}>
                  Review application
                </Button>
              </div>
              <p
                className={`save-feedback save-feedback-${saveStatus}`}
                role="status"
                aria-live="polite"
              >
                {saveMessage}
              </p>
            </div>
          ) : (
            <p className="notice">This questionnaire is read-only.</p>
          )}
        </form>
      )}
      {application.state !== "withdrawn" ? (
        <Button
          ref={withdrawButtonRef}
          type="button"
          className="button-danger"
          onClick={() => setWithdrawOpen(true)}
          disabled={busy}
        >
          Withdraw application
        </Button>
      ) : null}
      <ConfirmationDialog
        title="Withdraw this application?"
        open={withdrawOpen}
        onCancel={cancelWithdrawal}
        onConfirm={withdraw}
        confirmLabel="Withdraw application"
        cancelLabel="Keep application"
        dialogRef={dialogRef}
        busy={busy}
      >
        <p>
          Withdrawing ends this application attempt. You will not be able to
          edit it or upload new documents. You can continue to view retained
          application information while Keeper Financial retains it under the
          applicable retention policy.
        </p>
        <p>
          This action does not reopen the application. If the opportunity
          remains published, you may start a new application attempt.
        </p>
      </ConfirmationDialog>
    </div>
  );
}
