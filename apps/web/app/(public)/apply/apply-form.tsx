"use client";

import { useEffect, useRef, useState } from "react";
import { Button, ConsentCheckbox, ErrorSummary, FormField } from "@keeper/ui";

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
    required: "General mortgage objective is required.",
    invalid: "Select a valid general mortgage objective.",
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
  return fieldErrors;
}

export function ApplyForm({
  unavailableContact = "the published phone or email contact",
  preferredAgentSlug,
}: {
  unavailableContact?: string;
  preferredAgentSlug?: string;
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
      ...(preferredAgentSlug
        ? { preferred_agent_slug: preferredAgentSlug }
        : {}),
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
            "Check the required fields and remove sensitive or unsupported information.",
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
            `The contact service is temporarily unavailable. Please use ${unavailableContact}.`,
          ]);
        } else {
          setErrors([
            `The contact request could not be submitted right now. Please try again or use ${unavailableContact}.`,
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
      {preferredAgentSlug ? (
        <input
          type="hidden"
          name="preferred_agent_slug"
          value={preferredAgentSlug}
        />
      ) : null}
      <ErrorSummary errors={errors} />
      {submitted ? (
        <p role="status" aria-live="polite" className="notice notice-success">
          Thank you. Your minimal contact request was recorded. Keeper Financial
          can respond using your selected contact method.
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
          error={fieldErrors.telephone}
        >
          <input
            id="telephone"
            name="telephone"
            type="tel"
            autoComplete="tel"
            required
            minLength={7}
            maxLength={32}
            pattern="[0-9+().\- x]+"
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
          label="General mortgage objective"
          error={fieldErrors.mortgage_objective}
        >
          <select
            id="mortgage_objective"
            name="mortgage_objective"
            required
            defaultValue=""
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
        hint="Do not include your SIN, banking or card details, tax information, debts, identification, medical information, or passwords."
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
