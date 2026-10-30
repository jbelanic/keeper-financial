"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Button, ConsentCheckbox, ErrorSummary, FormField } from "@keeper/ui";
import {
  isAcceptablePhoneInput,
  PHONE_EXAMPLE,
  PHONE_INPUT_ERROR_INTERNATIONAL,
  PHONE_INPUT_PATTERN,
} from "@/lib/phone";

const VALIDATED_FIELDS = {
  name: {
    required: "Name is required.",
    invalid: "Name must contain at least 2 characters.",
  },
  email: {
    required: "Email is required.",
    invalid: "Enter a valid email address.",
  },
  telephone: {
    required: "Telephone is required.",
    invalid: "Enter a valid telephone number.",
  },
  preferred_contact_method: {
    required: "Preferred contact method is required.",
    invalid: "Select a valid preferred contact method.",
  },
  mortgage_objective: {
    required: "Mortgage goal is required.",
    invalid: "Select a valid mortgage goal.",
  },
  service_contact_acknowledged: {
    required: "Service-contact acknowledgement is required.",
    invalid: "Service-contact acknowledgement is required.",
  },
} as const;

type ValidatedField = keyof typeof VALIDATED_FIELDS;
type FieldErrors = Partial<Record<ValidatedField, string>>;

function validateFields(form: HTMLFormElement): FieldErrors {
  const fieldErrors: FieldErrors = {};
  for (const field of Object.keys(VALIDATED_FIELDS) as ValidatedField[]) {
    const control = form.elements.namedItem(field);
    if (
      !(
        control instanceof HTMLInputElement ||
        control instanceof HTMLSelectElement ||
        control instanceof HTMLTextAreaElement
      ) ||
      control.validity.valid
    ) {
      continue;
    }
    fieldErrors[field] = control.validity.valueMissing
      ? VALIDATED_FIELDS[field].required
      : VALIDATED_FIELDS[field].invalid;
  }
  const telephone = form.elements.namedItem("telephone");
  if (
    telephone instanceof HTMLInputElement &&
    telephone.value.trim() &&
    !isAcceptablePhoneInput(telephone.value)
  ) {
    // One clear sentence beats the browser's generic pattern complaint.
    fieldErrors.telephone = PHONE_INPUT_ERROR_INTERNATIONAL;
  }
  return fieldErrors;
}

export function ApplyForm({
  unavailableContact = "our phone number or email address",
  agentReference,
  objective,
  source = "website_readiness",
  followUp,
}: {
  unavailableContact?: string;
  agentReference?: string;
  /** Pre-fills the mortgage goal when a readiness card is chosen. */
  objective?: string;
  /** Capture surface recorded on the inquiry and its consent records. */
  source?: "website_apply" | "website_readiness";
  /** Extra sentence offering a phone or email route after a successful send. */
  followUp?: ReactNode;
}) {
  const [errors, setErrors] = useState<string[]>([]);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [submitted, setSubmitted] = useState(false);
  const [pending, setPending] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const submittingRef = useRef(false);

  useEffect(() => {
    if (errors.length > 0) {
      formRef.current?.querySelector<HTMLElement>(".error-summary")?.focus();
    }
  }, [errors]);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submittingRef.current) return;
    const formElement = event.currentTarget;
    setErrors([]);
    setFieldErrors({});
    setSubmitted(false);
    const invalidFields = validateFields(formElement);
    if (Object.keys(invalidFields).length > 0) {
      setFieldErrors(invalidFields);
      setErrors(Object.values(invalidFields));
      return;
    }
    submittingRef.current = true;
    setPending(true);
    const data = new FormData(formElement);
    const payload = {
      name: data.get("name"),
      email: data.get("email"),
      telephone: data.get("telephone"),
      mortgage_objective: data.get("mortgage_objective"),
      preferred_contact_method: data.get("preferred_contact_method"),
      source,
      ...(agentReference ? { agent_reference: agentReference } : {}),
      message: data.get("message") || null,
      service_contact_acknowledged:
        data.get("service_contact_acknowledged") === "on",
      marketing_consent: data.get("marketing_consent") === "on",
      website: data.get("website"),
    };
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"}/api/v1/leads`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      if (!response.ok) {
        if (response.status === 422) {
          setErrors([
            "Check the required fields and remove any sensitive details.",
          ]);
        } else if (response.status === 429) {
          const retryAfter = response.headers.get("Retry-After");
          setErrors([
            retryAfter && /^\d+$/.test(retryAfter)
              ? `Too many requests were received. Please wait ${retryAfter} seconds and try again.`
              : "Too many requests were received. Please wait a short while and try again.",
          ]);
        } else if (response.status === 503) {
          setErrors([
            "We couldn’t send your request right now. Nothing was submitted. Please try again shortly, or call or email us.",
          ]);
        } else {
          setErrors([
            "We could not send your request. Review the form and try again. If the problem continues, call or email us.",
          ]);
        }
        return;
      }
      formElement.reset();
      setSubmitted(true);
    } catch {
      setErrors([
        `The contact service is unavailable. Please use ${unavailableContact}.`,
      ]);
    } finally {
      submittingRef.current = false;
      setPending(false);
    }
  }

  return (
    <form ref={formRef} onSubmit={submit} noValidate aria-busy={pending}>
      <input type="hidden" name="website" value="" autoComplete="off" />
      {agentReference ? (
        <input type="hidden" name="agent_reference" value={agentReference} />
      ) : null}
      <ErrorSummary errors={errors} />
      {/* Owner + legal approved 2026-10-25 (decision 55(e)). Reword only on a new owner decision. */}
      {submitted ? (
        <p role="status" aria-live="polite" className="notice notice-success">
          Thank you. Your request has been received. We’ll follow up using your
          preferred contact method.{followUp ? <> {followUp}</> : null} For your
          protection, please don’t send documents by email; we’ll point you to
          the secure application if we need them.
        </p>
      ) : null}
      <div className="grid-2">
        <FormField id="name" label="Name" error={fieldErrors.name}>
          <input
            id="name"
            name="name"
            autoComplete="name"
            required
            maxLength={120}
          />
        </FormField>
        <FormField id="email" label="Email" error={fieldErrors.email}>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            maxLength={320}
          />
        </FormField>
        <FormField
          id="telephone"
          label="Telephone"
          hint={`10 digits is enough — for example ${PHONE_EXAMPLE}.`}
          error={fieldErrors.telephone}
        >
          <input
            id="telephone"
            name="telephone"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder={PHONE_EXAMPLE}
            required
            minLength={7}
            maxLength={32}
            pattern={PHONE_INPUT_PATTERN}
          />
        </FormField>
        <FormField
          id="preferred_contact_method"
          label="Preferred contact method"
          error={fieldErrors.preferred_contact_method}
        >
          <select
            id="preferred_contact_method"
            name="preferred_contact_method"
            required
            defaultValue=""
          >
            <option value="" disabled>
              Select one
            </option>
            <option value="email">Email</option>
            <option value="telephone">Telephone</option>
          </select>
        </FormField>
        <FormField
          id="mortgage_objective"
          label="Mortgage goal"
          hint="Choosing a goal above fills this in."
          error={fieldErrors.mortgage_objective}
        >
          <select
            id="mortgage_objective"
            name="mortgage_objective"
            required
            // The readiness cards own this value: remounting the field when it
            // changes is React's documented way to reset a form control from an
            // external source, without mirroring it into extra component state.
            key={objective ?? "none"}
            defaultValue={objective ?? ""}
          >
            <option value="" disabled>
              Select one
            </option>
            <option value="purchase">Purchase</option>
            <option value="refinance">Refinance</option>
            <option value="renewal">Renewal</option>
            <option value="investment">Investment property</option>
            <option value="other">Other</option>
          </select>
        </FormField>
      </div>
      <FormField
        id="message"
        label="Brief message (optional)"
        hint="Please don’t include your SIN or banking details here."
      >
        <textarea id="message" name="message" maxLength={1000} />
      </FormField>
      <ConsentCheckbox
        id="service_contact_acknowledged"
        required
        error={fieldErrors.service_contact_acknowledged}
      >
        I agree that Keeper Financial may contact me about this service inquiry.{" "}
        <strong>Required.</strong>
      </ConsentCheckbox>
      <ConsentCheckbox id="marketing_consent">
        I would also like optional marketing communications. This is separate
        and not required for service.
      </ConsentCheckbox>
      <Button type="submit" disabled={pending}>
        {pending ? "Sending…" : "Send contact request"}
      </Button>
    </form>
  );
}
