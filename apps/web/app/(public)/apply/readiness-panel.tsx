"use client";

import { useState } from "react";
import { Card, SectionHeading } from "@keeper/ui";
import { Icon } from "@/lib/public-components";
import { readinessGoals, readinessSteps } from "@/lib/public-content";
import { ApplyForm } from "./apply-form";

/**
 * The public contact details and application origin this surface needs. Kept
 * narrow so the server page resolves configuration and hands down plain values.
 */
export type ReadinessConfig = {
  phoneDisplay: string;
  phoneHref: string;
  email: string;
  emailHref: string;
  mortgageApplicationUrl: string;
  /** Owner-approved scheduling link, when one is configured. */
  bookingUrl?: string;
};

/**
 * The mortgage-readiness request surface. The six goal cards are only a shortcut
 * for the server-validated `mortgage_objective` field: choosing one fills the
 * request form below and never submits, navigates, or stores anything on its own.
 */
export function ReadinessPanel({
  agentReference,
  config,
}: {
  agentReference?: string;
  config: ReadinessConfig;
}) {
  const [selectedGoalId, setSelectedGoalId] = useState("");
  const objective = readinessGoals.find(
    (goal) => goal.id === selectedGoalId,
  )?.objective;
  const attribution = agentReference
    ? `?${new URLSearchParams({ agent: agentReference }).toString()}`
    : "";

  return (
    <>
      <section className="section section-no-top" id="readiness">
        <div className="container">
          <SectionHeading
            eyebrow="Mortgage readiness review"
            title="What would you like help with?"
            description="Pick the topic closest to where you are. It fills in the mortgage goal below — nothing is sent until you request the conversation."
          />
          <fieldset className="goal-fieldset">
            <legend className="visually-hidden">
              What would you like help with?
            </legend>
            <div className="goal-grid">
              {readinessGoals.map((goal) => (
                <label className="goal-option" key={goal.id}>
                  <input
                    type="radio"
                    name="readiness_goal"
                    value={goal.id}
                    checked={selectedGoalId === goal.id}
                    onChange={() => setSelectedGoalId(goal.id)}
                  />
                  <span>{goal.label}</span>
                </label>
              ))}
            </div>
          </fieldset>
        </div>
      </section>

      <section className="section section-muted">
        <div className="container process-layout">
          <SectionHeading
            eyebrow="What to expect"
            title="A conversation, then your decision."
            description="This is general guidance, not an application. Nobody can promise an approval, a specific rate, or an outcome before you share the details that affect them."
          />
          <ol className="process-list">
            {readinessSteps.map((step, index) => (
              <li key={step.title}>
                <span className="step-number" aria-hidden="true">
                  {index + 1}
                </span>
                <div>
                  <h3>{step.title}</h3>
                  <p>{step.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section">
        <div className="container apply-grid">
          <Card className="apply-card">
            <div className="card-icon">
              <Icon name="conversation" />
            </div>
            <p className="eyebrow">Option one</p>
            <h2>Request your mortgage readiness conversation</h2>
            <p>
              Tell us a little about what you’re planning. We’ll use your
              contact details to respond to your request.
            </p>
            <p className="contact-shortcuts">
              Prefer to call?{" "}
              <a href={config.phoneHref}>{config.phoneDisplay}</a>
              {config.bookingUrl ? (
                <>
                  {" "}
                  or <a href={config.bookingUrl}>Book a call</a>
                </>
              ) : null}
            </p>
            <ApplyForm
              agentReference={agentReference}
              objective={objective}
              unavailableContact={`${config.phoneDisplay} or ${config.email}`}
              followUp={
                <>
                  If you’d rather speak sooner, call{" "}
                  <a href={config.phoneHref}>{config.phoneDisplay}</a> or email{" "}
                  <a href={config.emailHref}>{config.email}</a>.
                  {config.bookingUrl ? (
                    <>
                      {" "}
                      You can also <a href={config.bookingUrl}>book a call</a>.
                    </>
                  ) : null}
                </>
              }
            />
          </Card>
          <Card className="apply-card secure-application-card">
            <div className="card-icon">
              <Icon name="shield" />
            </div>
            <p className="eyebrow">Option two</p>
            <h2>Ready to apply now?</h2>
            <p>
              If you’re ready to provide your mortgage application information,
              continue directly to Keeper Financial’s secure application. Start
              your private application for the financial, identity and property
              details we’ll need. It saves as you go in this browser only.
            </p>
            <a
              className="button-link"
              href={`${config.mortgageApplicationUrl}${attribution}`}
            >
              Start Your Application
            </a>
            <p className="fine-print">
              Saved as you go. Your draft resumes only in this browser while its
              secure cookie remains available, so please don’t use a shared or
              public device. If the application is unavailable, call{" "}
              {config.phoneDisplay} or email {config.email}.
            </p>
          </Card>
        </div>
      </section>
    </>
  );
}
