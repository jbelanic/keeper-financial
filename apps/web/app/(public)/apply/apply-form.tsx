"use client";

import { useState } from "react";
import { Button, ConsentCheckbox, ErrorSummary, FormField } from "@keeper/ui";

export function ApplyForm() {
  const [errors, setErrors] = useState<string[]>([]);
  const [submitted, setSubmitted] = useState(false);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    setErrors([]);
    setSubmitted(false);
    const data = new FormData(formElement);
    const payload = {
      name: data.get("name"),
      email: data.get("email"),
      telephone: data.get("telephone"),
      mortgage_objective: data.get("mortgage_objective"),
      preferred_contact_method: data.get("preferred_contact_method"),
      preferred_agent_slug: data.get("preferred_agent_slug") || null,
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
        const problem = (await response.json()) as {
          detail?: Array<{ msg?: string }> | string;
        };
        const details = Array.isArray(problem.detail)
          ? problem.detail.map((item) => item.msg ?? "Invalid value")
          : [
              typeof problem.detail === "string"
                ? problem.detail
                : "The inquiry could not be submitted.",
            ];
        setErrors(details);
        return;
      }
      formElement.reset();
      setSubmitted(true);
    } catch {
      setErrors([
        "The contact service is unavailable. Please use the approved telephone contact once published.",
      ]);
    }
  }

  return (
    <form onSubmit={submit} noValidate>
      <input type="hidden" name="website" value="" autoComplete="off" />
      <ErrorSummary errors={errors} />
      {submitted ? (
        <p role="status" className="notice">
          Thank you. Your minimal-contact inquiry was recorded.
        </p>
      ) : null}
      <div className="grid-2">
        <FormField id="name" label="Name">
          <input
            id="name"
            name="name"
            autoComplete="name"
            required
            maxLength={120}
          />
        </FormField>
        <FormField id="email" label="Email">
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            maxLength={320}
          />
        </FormField>
        <FormField id="telephone" label="Telephone">
          <input
            id="telephone"
            name="telephone"
            type="tel"
            autoComplete="tel"
            required
            maxLength={32}
          />
        </FormField>
        <FormField
          id="preferred_contact_method"
          label="Preferred contact method"
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
        <FormField id="mortgage_objective" label="General mortgage objective">
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
        <FormField
          id="preferred_agent_slug"
          label="Preferred agent (optional)"
          hint="Use an approved agent profile identifier only."
        >
          <input
            id="preferred_agent_slug"
            name="preferred_agent_slug"
            maxLength={100}
            pattern="[a-z0-9-]+"
          />
        </FormField>
      </div>
      <FormField
        id="message"
        label="Brief message (optional)"
        hint="Do not include your SIN, banking or card details, tax information, debts, identification, medical information, or passwords."
      >
        <textarea id="message" name="message" maxLength={1000} />
      </FormField>
      <ConsentCheckbox id="service_contact_acknowledged" required>
        I agree that Keeper Financial may contact me about this service inquiry.{" "}
        <strong>Required.</strong>
      </ConsentCheckbox>
      <ConsentCheckbox id="marketing_consent">
        I would also like optional marketing communications. This is separate
        and not required for service.
      </ConsentCheckbox>
      <Button type="submit">Send contact request</Button>
    </form>
  );
}
