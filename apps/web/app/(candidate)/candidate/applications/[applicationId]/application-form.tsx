"use client";

import { useEffect, useRef, useState } from "react";
import {
  Button,
  ConfirmationDialog,
  ErrorSummary,
  FormField,
  StatusBadge,
} from "@keeper/ui";
import { candidateBrowserJson } from "@/lib/candidate-browser-api";
import type {
  CandidateApplication,
  CandidatePrivacyDisclosure,
} from "@/lib/recruitment-api";

type Employment = CandidateApplication["employment"][number];
type Education = CandidateApplication["education"][number];
const sensitiveWarning =
  "Do not include identification numbers, financial or health information, passwords, background-check information, licence numbers, or anything not requested.";

function value(form: FormData, name: string): string | null {
  const result = String(form.get(name) ?? "").trim();
  return result || null;
}

function requiredErrors(form: FormData): string[] {
  const checks: Array<[string, string]> = [
    ["given_name", "First/given name"],
    ["family_name", "Last/family name"],
    ["phone", "Phone number"],
    ["city", "City"],
    ["country_code", "Country"],
    ["preferred_contact_method", "Preferred contact method"],
  ];
  const errors = checks
    .filter(([name]) => !value(form, name))
    .map(([, label]) => `${label} is required.`);
  const interest = value(form, "interest_statement") ?? "";
  if (interest.length < 100)
    errors.push("Interest statement must contain at least 100 characters.");
  if (form.get("privacy_acknowledged") !== "on")
    errors.push("You must acknowledge the candidate privacy disclosure.");
  if (form.get("information_accuracy_confirmed") !== "on")
    errors.push("You must confirm the information is accurate.");
  return errors;
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
  const [errors, setErrors] = useState<string[]>([]);
  const [notice, setNotice] = useState("");
  const [reviewing, setReviewing] = useState(false);
  const [busy, setBusy] = useState(false);
  const [withdrawOpen, setWithdrawOpen] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const withdrawButtonRef = useRef<HTMLButtonElement>(null);
  const noticeRef = useRef<HTMLParagraphElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const editable = application.state === "draft";
  const fieldError = (prefix: string) =>
    errors.find((error) => error.startsWith(prefix));

  useEffect(() => {
    if (errors.length) {
      document.querySelector<HTMLElement>(".error-summary")?.focus();
    }
  }, [errors]);

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
      referral_source: value(form, "referral_source"),
      referral_detail: value(form, "referral_detail"),
      interest_statement: value(form, "interest_statement"),
      relevant_experience: value(form, "relevant_experience"),
      employment,
      education,
      privacy_acknowledged: form.get("privacy_acknowledged") === "on",
      information_accuracy_confirmed:
        form.get("information_accuracy_confirmed") === "on",
    };
  }

  async function saveDraft() {
    if (!formRef.current || busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Saving draft…");
    try {
      const updated = await requestJson(
        `/api/v1/candidate/applications/${application.id}`,
        {
          method: "PATCH",
          body: JSON.stringify(draftPayload(new FormData(formRef.current))),
        },
      );
      setApplication(updated);
      setNotice("Draft saved.");
    } catch {
      setErrors([
        "The draft could not be saved. Your current page has not been submitted.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function review(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = new FormData(event.currentTarget);
    const nextErrors = requiredErrors(form);
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
    } catch {
      setErrors([
        "The draft could not be saved for review. The application has not been submitted.",
      ]);
      setNotice("");
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
    } catch {
      setErrors([
        "The application was not submitted. Save the draft and review any changed fields.",
      ]);
      setNotice("");
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
      setErrors(["The application could not be withdrawn."]);
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
      <nav className="progress-nav" aria-label="Application progress">
        <ol>
          <li>Opportunity</li>
          <li>Contact information</li>
          <li>Application details</li>
          <li>Optional history</li>
          <li>Privacy and review</li>
        </ol>
      </nav>
      <p>
        Current status:{" "}
        <StatusBadge>{application.status.replaceAll("_", " ")}</StatusBadge>
      </p>
      <p aria-live="polite" role="status" tabIndex={-1} ref={noticeRef}>
        {notice}
      </p>
      <ErrorSummary errors={errors} />
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
                error={fieldError("First/given name")}
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
                error={fieldError("Last/family name")}
              >
                <input
                  id="family_name"
                  name="family_name"
                  defaultValue={application.family_name ?? ""}
                  maxLength={70}
                  required
                />
              </FormField>
              <FormField id="preferred_name" label="Preferred name (optional)">
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
                hint="Include the country code, for example +1 416 555 0100."
                error={fieldError("Phone number")}
              >
                <input
                  id="phone"
                  name="phone"
                  type="tel"
                  defaultValue={application.phone ?? ""}
                  maxLength={32}
                  required
                />
              </FormField>
              <FormField
                id="city"
                label="City (required)"
                error={fieldError("City")}
              >
                <input
                  id="city"
                  name="city"
                  defaultValue={application.city ?? ""}
                  maxLength={100}
                  required
                />
              </FormField>
              <FormField id="region" label="Province/state/region (optional)">
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
                hint="Two-letter ISO country code."
                error={fieldError("Country")}
              >
                <input
                  id="country_code"
                  name="country_code"
                  defaultValue={application.country_code ?? "CA"}
                  minLength={2}
                  maxLength={2}
                  required
                />
              </FormField>
              <FormField
                id="preferred_contact_method"
                label="Preferred contact method (required)"
                error={fieldError("Preferred contact method")}
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
            >
              <select
                id="referral_source"
                name="referral_source"
                defaultValue={application.referral_source ?? ""}
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
            <FormField
              id="referral_detail"
              label="Referral details (optional)"
              hint="Available only for a referral or other source."
            >
              <input
                id="referral_detail"
                name="referral_detail"
                defaultValue={application.referral_detail ?? ""}
                maxLength={120}
              />
            </FormField>
            <FormField
              id="interest_statement"
              label="Why are you interested in this opportunity? (required)"
              hint={sensitiveWarning}
              error={fieldError("Interest statement")}
            >
              <textarea
                id="interest_statement"
                name="interest_statement"
                defaultValue={application.interest_statement ?? ""}
                minLength={100}
                maxLength={2000}
                required
              />
            </FormField>
            <FormField
              id="relevant_experience"
              label="Relevant experience (optional)"
              hint={sensitiveWarning}
            >
              <textarea
                id="relevant_experience"
                name="relevant_experience"
                defaultValue={application.relevant_experience ?? ""}
                maxLength={2000}
              />
            </FormField>
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
                >
                  <input
                    id={`employer-${index}`}
                    value={entry.employer_name}
                    maxLength={160}
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
                >
                  <input
                    id={`role-${index}`}
                    value={entry.role_title}
                    maxLength={160}
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
                >
                  <input
                    id={`start-${index}`}
                    type="month"
                    value={entry.start_month}
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
                <label className="consent">
                  <input
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
                  >
                    <input
                      id={`end-${index}`}
                      type="month"
                      value={entry.end_month ?? ""}
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
                  hint={sensitiveWarning}
                >
                  <textarea
                    id={`employment-summary-${index}`}
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
                >
                  <input
                    id={`institution-${index}`}
                    value={entry.institution_name}
                    maxLength={160}
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
                >
                  <input
                    id={`program-${index}`}
                    value={entry.program_name}
                    maxLength={160}
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
                >
                  <input
                    id={`completion-${index}`}
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
                name="privacy_acknowledged"
                type="checkbox"
                defaultChecked={application.privacy_acknowledged}
                aria-describedby={
                  fieldError("You must acknowledge")
                    ? "privacy-acknowledged-error"
                    : undefined
                }
                aria-invalid={
                  fieldError("You must acknowledge") ? true : undefined
                }
              />
              I have read the candidate privacy disclosure (required for
              submission)
            </label>
            {fieldError("You must acknowledge") ? (
              <p id="privacy-acknowledged-error" className="field-error">
                {fieldError("You must acknowledge")}
              </p>
            ) : null}
            <label className="consent">
              <input
                name="information_accuracy_confirmed"
                type="checkbox"
                defaultChecked={application.information_accuracy_confirmed}
                aria-describedby={
                  fieldError("You must confirm")
                    ? "accuracy-confirmed-error"
                    : undefined
                }
                aria-invalid={fieldError("You must confirm") ? true : undefined}
              />
              I confirm that the information I am submitting is accurate to the
              best of my knowledge (required for submission)
            </label>
            {fieldError("You must confirm") ? (
              <p id="accuracy-confirmed-error" className="field-error">
                {fieldError("You must confirm")}
              </p>
            ) : null}
            <p>
              This accuracy confirmation is not an electronic signature,
              licensing attestation, background consent, identity verification,
              or suitability declaration.
            </p>
          </fieldset>
          {editable ? (
            <div className="button-row">
              <Button type="button" onClick={saveDraft} disabled={busy}>
                Save draft
              </Button>
              <Button type="submit" disabled={busy}>
                Review application
              </Button>
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
        dialogRef={dialogRef}
        busy={busy}
      >
        <p>
          Withdrawal ends editing and new uploads. Your retained application and
          eligible documents remain available read-only under the approved
          policy.
        </p>
      </ConfirmationDialog>
    </div>
  );
}
