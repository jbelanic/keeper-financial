"use client";

import { useState } from "react";
import { Button, Card, ErrorSummary, FormField, StatusBadge } from "@keeper/ui";
import { adminBrowserRequest } from "@/lib/admin-browser-api";
import type {
  PlanSummary,
  PlanWithTasks,
  PlanCreateIn,
  ActivationGateResponse,
} from "@/lib/review-onboarding-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

export function OnboardingAdmin({
  initialPlans,
  requester = adminBrowserRequest,
}: {
  initialPlans: PlanSummary[];
  requester?: Requester;
}) {
  const [plans, setPlans] = useState<PlanSummary[]>(initialPlans);
  const [expanded, setExpanded] = useState<PlanWithTasks | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  const [planName, setPlanName] = useState("");
  const [planDescription, setPlanDescription] = useState("");

  const [assignCandidateId, setAssignCandidateId] = useState("");
  const [assignApplicationId, setAssignApplicationId] = useState("");
  const [assignPlanId, setAssignPlanId] = useState("");

  const [gateCandidateId, setGateCandidateId] = useState("");
  const [gateCode, setGateCode] = useState("");
  const [gateStatus, setGateStatus] = useState<ActivationGateResponse | null>(
    null,
  );

  const [esignCandidateId, setEsignCandidateId] = useState("");
  const [esignUrl, setEsignUrl] = useState("");

  async function createPlan(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Creating plan…");
    const payload: PlanCreateIn = {
      name: planName.trim(),
      description: planDescription.trim(),
      tasks: [],
    };
    try {
      const response = await requester("/api/v1/admin/onboarding/plans", {
        method: "POST",
        body: JSON.stringify(payload),
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) throw new Error("rejected");
      const plan = (await response.json()) as PlanSummary;
      setPlans((items) => [plan, ...items]);
      setPlanName("");
      setPlanDescription("");
      setNotice("Onboarding plan created.");
    } catch {
      setErrors(["The plan could not be created."]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function viewPlan(planId: string) {
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/plans/${planId}`,
      );
      if (!response.ok) throw new Error("rejected");
      setExpanded((await response.json()) as PlanWithTasks);
    } catch {
      setErrors(["Could not load plan detail."]);
    } finally {
      setBusy(false);
    }
  }

  async function assignPlan(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Assigning plan…");
    try {
      const response = await requester(
        `/api/v1/admin/candidates/${encodeURIComponent(assignCandidateId)}/assign-onboarding?plan_id=${encodeURIComponent(assignPlanId)}&application_id=${encodeURIComponent(assignApplicationId)}`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error("rejected");
      setNotice("Onboarding plan assigned to candidate.");
    } catch {
      setErrors([
        "Assignment was rejected. Confirm the candidate is in a selectable status and the plan is active.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function satisfyGate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setGateStatus(null);
    setNotice("Satisfying gate…");
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/candidates/${gateCandidateId}/gates`,
        {
          method: "POST",
          body: JSON.stringify({ code: gateCode.trim() }),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("rejected");
      setGateStatus((await response.json()) as ActivationGateResponse);
      setNotice("Activation gate satisfied.");
    } catch {
      setErrors([
        "Gate could not be satisfied. Confirm the candidate and a valid gate code.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function linkEnvelope(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Linking e-sign envelope…");
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/candidates/${esignCandidateId}/esign-envelopes`,
        {
          method: "POST",
          body: JSON.stringify({
            envelope_url: esignUrl.trim(),
            envelope_id: null,
            status: "sent",
          }),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("rejected");
      setNotice("External e-sign envelope linked.");
    } catch {
      setErrors(["The envelope link could not be stored."]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="onboarding-admin">
      <p role="status" aria-live="polite">
        {notice}
      </p>
      <ErrorSummary errors={errors} />

      <section aria-labelledby="plans-heading">
        <h2 id="plans-heading">Onboarding plans</h2>
        <form className="card" onSubmit={createPlan} aria-busy={busy}>
          <h3>Create plan template</h3>
          <FormField id="plan-name" label="Plan name (required)">
            <input
              id="plan-name"
              value={planName}
              maxLength={160}
              onChange={(event) => setPlanName(event.target.value)}
              required
            />
          </FormField>
          <FormField id="plan-description" label="Description">
            <textarea
              id="plan-description"
              value={planDescription}
              maxLength={1000}
              onChange={(event) => setPlanDescription(event.target.value)}
            />
          </FormField>
          <div className="button-row">
            <Button type="submit" disabled={busy}>
              Create plan
            </Button>
          </div>
        </form>

        {plans.length === 0 ? (
          <p>No onboarding plans have been created.</p>
        ) : (
          <ul className="grid-2">
            {plans.map((plan) => (
              <li key={plan.id}>
                <Card>
                  <h3>{plan.name}</h3>
                  <p>{plan.description}</p>
                  <p>
                    Status:{" "}
                    <StatusBadge tone={plan.is_active ? "success" : "neutral"}>
                      {plan.is_active ? "active" : "inactive"}
                    </StatusBadge>
                  </p>
                  <div className="button-row">
                    <Button
                      type="button"
                      onClick={() => viewPlan(plan.id)}
                      disabled={busy}
                    >
                      View tasks
                    </Button>
                  </div>
                </Card>
              </li>
            ))}
          </ul>
        )}

        {expanded ? (
          <Card aria-labelledby="plan-detail-heading">
            <h3 id="plan-detail-heading">{expanded.name} tasks</h3>
            {expanded.tasks && expanded.tasks.length > 0 ? (
              <ol>
                {expanded.tasks.map((task) => (
                  <li key={task.id}>
                    {task.title}
                    {task.instructions ? ` — ${task.instructions}` : ""}
                  </li>
                ))}
              </ol>
            ) : (
              <p>This plan has no tasks yet.</p>
            )}
          </Card>
        ) : null}
      </section>

      <section aria-labelledby="assign-heading">
        <h2 id="assign-heading">Assign plan</h2>
        <form className="card" onSubmit={assignPlan} aria-busy={busy}>
          <FormField id="assign-candidate" label="Candidate ID (required)">
            <input
              id="assign-candidate"
              value={assignCandidateId}
              onChange={(event) => setAssignCandidateId(event.target.value)}
              required
            />
          </FormField>
          <FormField id="assign-plan" label="Plan ID (required)">
            <input
              id="assign-plan"
              value={assignPlanId}
              onChange={(event) => setAssignPlanId(event.target.value)}
              required
            />
          </FormField>
          <FormField
            id="assign-application"
            label="Conditionally selected application ID (required)"
          >
            <input
              id="assign-application"
              value={assignApplicationId}
              onChange={(event) => setAssignApplicationId(event.target.value)}
              required
            />
          </FormField>
          <div className="button-row">
            <Button type="submit" disabled={busy}>
              Assign plan
            </Button>
          </div>
        </form>
      </section>

      <section aria-labelledby="gate-heading">
        <h2 id="gate-heading">Satisfy activation gate</h2>
        <form className="card" onSubmit={satisfyGate} aria-busy={busy}>
          <FormField id="gate-candidate" label="Candidate ID (required)">
            <input
              id="gate-candidate"
              value={gateCandidateId}
              onChange={(event) => setGateCandidateId(event.target.value)}
              required
            />
          </FormField>
          <FormField
            id="gate-code"
            label="Gate code (required)"
            hint="Server-owned gate, e.g. background_check."
          >
            <input
              id="gate-code"
              value={gateCode}
              onChange={(event) => setGateCode(event.target.value)}
              required
            />
          </FormField>
          <div className="button-row">
            <Button type="submit" disabled={busy}>
              Satisfy gate
            </Button>
          </div>
          {gateStatus ? (
            <p>
              Gate <strong>{gateStatus.code}</strong> is now{" "}
              <StatusBadge
                tone={gateStatus.status === "satisfied" ? "success" : "warning"}
              >
                {gateStatus.status}
              </StatusBadge>
              .
            </p>
          ) : null}
        </form>
      </section>

      <section aria-labelledby="esign-heading">
        <h2 id="esign-heading">External e-sign envelope</h2>
        <form className="card" onSubmit={linkEnvelope} aria-busy={busy}>
          <FormField id="esign-candidate" label="Candidate ID (required)">
            <input
              id="esign-candidate"
              value={esignCandidateId}
              onChange={(event) => setEsignCandidateId(event.target.value)}
              required
            />
          </FormField>
          <FormField
            id="esign-url"
            label="Envelope URL (required)"
            hint="Link to the externally hosted e-signature envelope. No signature is created here."
          >
            <input
              id="esign-url"
              type="url"
              value={esignUrl}
              maxLength={2048}
              onChange={(event) => setEsignUrl(event.target.value)}
              required
            />
          </FormField>
          <div className="button-row">
            <Button type="submit" disabled={busy}>
              Link envelope
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
}
