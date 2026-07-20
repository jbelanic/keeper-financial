"use client";

import { useState } from "react";
import { Button, Card, ErrorSummary, FormField, StatusBadge } from "@keeper/ui";
import { adminBrowserRequest } from "@/lib/admin-browser-api";
import type {
  AdminOnboardingAssignmentDetail,
  AdminOnboardingAssignmentSummary,
  PlanCreateIn,
  PlanSummary,
  PlanWithTasks,
} from "@/lib/review-onboarding-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;
type DraftTask = {
  title: string;
  instructions: string;
  is_required: boolean;
};

const emptyTask = (): DraftTask => ({
  title: "",
  instructions: "",
  is_required: true,
});

const assignmentStatusLabel = (status: string) =>
  `${status.charAt(0).toUpperCase()}${status.slice(1)} assignment`;

export function OnboardingAdmin({
  initialPlans,
  initialAssignments,
  requester = adminBrowserRequest,
}: {
  initialPlans: PlanSummary[];
  initialAssignments: AdminOnboardingAssignmentSummary[];
  requester?: Requester;
}) {
  const [plans, setPlans] = useState(initialPlans);
  const [assignments] = useState(initialAssignments);
  const [expanded, setExpanded] = useState<PlanWithTasks | null>(null);
  const [detail, setDetail] = useState<AdminOnboardingAssignmentDetail | null>(
    null,
  );
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [editingPlanId, setEditingPlanId] = useState("");
  const [planName, setPlanName] = useState("");
  const [planDescription, setPlanDescription] = useState("");
  const [tasks, setTasks] = useState<DraftTask[]>([emptyTask()]);
  const [gateCode, setGateCode] = useState("");
  const [gateAction, setGateAction] = useState<"satisfy" | "reopen">("satisfy");
  const [verifiedOn, setVerifiedOn] = useState("");
  const [evidenceSource, setEvidenceSource] = useState("");
  const [evidenceReference, setEvidenceReference] = useState("");
  const [reopenReason, setReopenReason] = useState("");
  const [envelopeId, setEnvelopeId] = useState("");
  const [replacementRecordId, setReplacementRecordId] = useState("");

  function fail(message: string) {
    setErrors([message]);
    setNotice("");
  }

  async function loadAssignment(assignmentId: string) {
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/assignments/${encodeURIComponent(assignmentId)}`,
      );
      if (!response.ok) throw new Error("rejected");
      setDetail((await response.json()) as AdminOnboardingAssignmentDetail);
    } catch {
      fail("The onboarding assignment could not be loaded.");
    } finally {
      setBusy(false);
    }
  }

  function resetPlanEditor() {
    setEditingPlanId("");
    setPlanName("");
    setPlanDescription("");
    setTasks([emptyTask()]);
  }

  async function savePlan(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice(editingPlanId ? "Saving plan changes…" : "Creating plan…");
    const payload: PlanCreateIn = {
      name: planName.trim(),
      description: planDescription.trim(),
      tasks: tasks.map((task) => ({
        title: task.title.trim(),
        instructions: task.instructions.trim(),
        is_required: task.is_required,
      })),
    };
    try {
      const response = await requester(
        editingPlanId
          ? `/api/v1/admin/onboarding/plans/${encodeURIComponent(editingPlanId)}`
          : "/api/v1/admin/onboarding/plans",
        {
          method: editingPlanId ? "PATCH" : "POST",
          body: JSON.stringify(payload),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("rejected");
      const plan = (await response.json()) as PlanWithTasks;
      setPlans((items) =>
        editingPlanId
          ? items.map((item) => (item.id === plan.id ? plan : item))
          : [plan, ...items],
      );
      setExpanded(plan);
      setNotice(
        editingPlanId
          ? "Unused onboarding plan updated."
          : "Onboarding plan created. It remains editable until its first assignment.",
      );
      resetPlanEditor();
    } catch {
      fail(
        editingPlanId
          ? "The plan could not be updated. It may already be assigned."
          : "The plan could not be created. Check every required task title.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function viewPlan(planId: string) {
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/plans/${encodeURIComponent(planId)}`,
      );
      if (!response.ok) throw new Error("rejected");
      setExpanded((await response.json()) as PlanWithTasks);
    } catch {
      fail("The plan detail could not be loaded.");
    } finally {
      setBusy(false);
    }
  }

  async function editPlan(plan: PlanSummary) {
    if (plan.is_locked) return;
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/plans/${encodeURIComponent(plan.id)}`,
      );
      if (!response.ok) throw new Error("rejected");
      const loaded = (await response.json()) as PlanWithTasks;
      if (loaded.is_locked) {
        fail("The plan has already been assigned and is now immutable.");
        return;
      }
      setEditingPlanId(loaded.id);
      setPlanName(loaded.name);
      setPlanDescription(loaded.description);
      const loadedTasks = loaded.tasks ?? [];
      setTasks(
        loadedTasks.length > 0
          ? loadedTasks.map((task) => ({
              title: task.title,
              instructions: task.instructions,
              is_required: task.is_required,
            }))
          : [emptyTask()],
      );
      setExpanded(null);
      setNotice("Editing unused onboarding plan.");
    } catch {
      fail("The plan could not be loaded for editing.");
    } finally {
      setBusy(false);
    }
  }

  async function togglePlan(plan: PlanSummary) {
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/plans/${plan.id}/availability`,
        {
          method: "PATCH",
          body: JSON.stringify({ is_active: !plan.is_active }),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("rejected");
      const updated = (await response.json()) as PlanWithTasks;
      setPlans((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
      setNotice(updated.is_active ? "Plan reactivated." : "Plan deactivated.");
    } catch {
      fail("The plan availability could not be changed.");
    } finally {
      setBusy(false);
    }
  }

  function updateTask(index: number, change: Partial<DraftTask>) {
    setTasks((items) =>
      items.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...change } : item,
      ),
    );
  }

  function moveTask(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= tasks.length) return;
    setTasks((items) => {
      const next = [...items];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  async function submitGate(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail || busy) return;
    setBusy(true);
    setErrors([]);
    try {
      const body =
        gateAction === "satisfy"
          ? {
              verified_on: verifiedOn,
              evidence_source: evidenceSource.trim(),
              evidence_reference: evidenceReference.trim(),
            }
          : { reason: reopenReason.trim() };
      const response = await requester(
        `/api/v1/admin/onboarding/assignments/${detail.assignment_id}/gates/${encodeURIComponent(gateCode)}/${gateAction}`,
        {
          method: "POST",
          body: JSON.stringify(body),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("rejected");
      await loadAssignment(detail.assignment_id);
      setNotice(
        gateAction === "satisfy" ? "Gate evidence recorded." : "Gate reopened.",
      );
      setGateCode("");
      setReopenReason("");
    } catch {
      fail(
        "The gate change was rejected. Derived gates cannot be changed manually.",
      );
      setBusy(false);
    }
  }

  async function linkEnvelope(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!detail || busy) return;
    setBusy(true);
    setErrors([]);
    const replacing = Boolean(replacementRecordId);
    const path = replacing
      ? `/api/v1/admin/onboarding/assignments/${detail.assignment_id}/esign-envelopes/${replacementRecordId}/replace`
      : `/api/v1/admin/onboarding/assignments/${detail.assignment_id}/esign-envelopes`;
    try {
      const response = await requester(path, {
        method: "POST",
        body: JSON.stringify({ provider_envelope_id: envelopeId.trim() }),
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) throw new Error("rejected");
      await loadAssignment(detail.assignment_id);
      setEnvelopeId("");
      setReplacementRecordId("");
      setNotice(
        replacing
          ? "Replacement envelope linked."
          : "Documenso envelope linked.",
      );
    } catch {
      fail("The Documenso envelope could not be linked.");
      setBusy(false);
    }
  }

  async function refreshEnvelope(recordId: string) {
    if (!detail || busy) return;
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/assignments/${detail.assignment_id}/esign-envelopes/${recordId}/refresh`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error("rejected");
      await loadAssignment(detail.assignment_id);
      setNotice("Envelope status verified with Documenso.");
    } catch {
      fail(
        "Documenso status could not be verified; readiness remains fail-closed.",
      );
      setBusy(false);
    }
  }

  async function reviewTask(taskId: string, approved: boolean) {
    if (!detail || busy) return;
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/onboarding/candidates/${detail.candidate_id}/tasks/${taskId}/review`,
        {
          method: "POST",
          body: JSON.stringify({ approved, review_notes: null }),
          headers: { "Content-Type": "application/json" },
        },
      );
      if (!response.ok) throw new Error("rejected");
      await loadAssignment(detail.assignment_id);
      setNotice(
        approved ? "Task approved." : "Task returned to the candidate.",
      );
    } catch {
      fail("The task review could not be recorded.");
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
        <h2 id="plans-heading">Onboarding plan templates</h2>
        <p>
          Build and revise the ordered task list before assignment. The first
          assignment permanently locks the plan content and availability.
        </p>
        <form className="card" onSubmit={savePlan} aria-busy={busy}>
          <h3>
            {editingPlanId ? "Edit unused plan" : "Create onboarding plan"}
          </h3>
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
          <fieldset>
            <legend>Ordered onboarding tasks</legend>
            {tasks.map((task, index) => (
              <Card key={index}>
                <h4>Task {index + 1}</h4>
                <FormField
                  id={`task-title-${index}`}
                  label="Task title (required)"
                >
                  <input
                    id={`task-title-${index}`}
                    value={task.title}
                    maxLength={160}
                    onChange={(event) =>
                      updateTask(index, { title: event.target.value })
                    }
                    required
                  />
                </FormField>
                <FormField
                  id={`task-instructions-${index}`}
                  label="Instructions"
                >
                  <textarea
                    id={`task-instructions-${index}`}
                    value={task.instructions}
                    maxLength={2000}
                    onChange={(event) =>
                      updateTask(index, { instructions: event.target.value })
                    }
                  />
                </FormField>
                <label>
                  <input
                    type="checkbox"
                    checked={task.is_required}
                    onChange={(event) =>
                      updateTask(index, { is_required: event.target.checked })
                    }
                  />{" "}
                  Required for readiness
                </label>
                <div className="button-row">
                  <Button
                    type="button"
                    disabled={index === 0 || busy}
                    onClick={() => moveTask(index, -1)}
                  >
                    Move up
                  </Button>
                  <Button
                    type="button"
                    disabled={index === tasks.length - 1 || busy}
                    onClick={() => moveTask(index, 1)}
                  >
                    Move down
                  </Button>
                  <Button
                    type="button"
                    disabled={tasks.length === 1 || busy}
                    onClick={() =>
                      setTasks((items) =>
                        items.filter((_, itemIndex) => itemIndex !== index),
                      )
                    }
                  >
                    Remove task
                  </Button>
                </div>
              </Card>
            ))}
          </fieldset>
          <div className="button-row">
            <Button
              type="button"
              disabled={busy}
              onClick={() => setTasks((items) => [...items, emptyTask()])}
            >
              Add task
            </Button>
            <Button type="submit" disabled={busy}>
              {editingPlanId ? "Save plan changes" : "Create plan"}
            </Button>
            {editingPlanId ? (
              <Button type="button" disabled={busy} onClick={resetPlanEditor}>
                Cancel edit
              </Button>
            ) : null}
          </div>
        </form>

        <ul className="grid-2">
          {plans.map((plan) => (
            <li key={plan.id}>
              <Card>
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
                <StatusBadge tone={plan.is_active ? "success" : "neutral"}>
                  {plan.is_active ? "active" : "inactive"}
                </StatusBadge>
                {plan.is_locked ? (
                  <p>
                    <strong>Locked after first assignment.</strong>
                  </p>
                ) : (
                  <p>Editable until first assignment.</p>
                )}
                <div className="button-row">
                  <Button
                    type="button"
                    onClick={() => viewPlan(plan.id)}
                    disabled={busy}
                  >
                    View tasks
                  </Button>
                  {!plan.is_locked ? (
                    <Button
                      type="button"
                      onClick={() => editPlan(plan)}
                      disabled={busy}
                    >
                      Edit plan
                    </Button>
                  ) : null}
                  {!plan.is_locked ? (
                    <Button
                      type="button"
                      onClick={() => togglePlan(plan)}
                      disabled={busy}
                    >
                      {plan.is_active ? "Deactivate plan" : "Reactivate plan"}
                    </Button>
                  ) : null}
                </div>
              </Card>
            </li>
          ))}
        </ul>
        {expanded ? (
          <Card>
            <h3>
              {expanded.name} —{" "}
              {expanded.is_locked ? "locked task order" : "editable task order"}
            </h3>
            <ol>
              {(expanded.tasks ?? []).map((task) => (
                <li key={task.id}>
                  <strong>{task.title}</strong>
                  {task.instructions ? ` — ${task.instructions}` : ""}
                </li>
              ))}
            </ol>
          </Card>
        ) : null}
      </section>

      <section aria-labelledby="assignments-heading">
        <h2 id="assignments-heading">Candidate onboarding assignments</h2>
        {assignments.length === 0 ? (
          <p>No onboarding assignments are available.</p>
        ) : (
          <ul className="grid-2">
            {assignments.map((assignment) => (
              <li key={assignment.assignment_id}>
                <Card>
                  <h3>{assignment.candidate_name}</h3>
                  <p>{assignment.candidate_email}</p>
                  <p>
                    {assignment.opportunity_title} — attempt{" "}
                    {assignment.attempt_number}
                  </p>
                  <p>Plan: {assignment.plan_name}</p>
                  <StatusBadge
                    tone={
                      assignment.status === "active" ? "success" : "warning"
                    }
                  >
                    {assignmentStatusLabel(assignment.status)}
                  </StatusBadge>
                  {assignment.status === "active" ? (
                    <StatusBadge
                      tone={assignment.activation_ready ? "success" : "warning"}
                    >
                      {assignment.activation_ready
                        ? "readiness gates satisfied"
                        : "not activation-ready"}
                    </StatusBadge>
                  ) : null}
                  <Button
                    type="button"
                    onClick={() => loadAssignment(assignment.assignment_id)}
                    disabled={busy}
                  >
                    {assignment.status === "active"
                      ? "Manage active assignment"
                      : "View assignment history"}
                  </Button>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      {detail ? (
        <section aria-labelledby="assignment-detail-heading">
          <h2 id="assignment-detail-heading">
            {detail.candidate_name} onboarding
          </h2>
          <p>
            {detail.opportunity_title} — attempt {detail.attempt_number}; plan{" "}
            {detail.plan_name}
          </p>
          <StatusBadge
            tone={detail.status === "active" ? "success" : "warning"}
          >
            {assignmentStatusLabel(detail.status)}
          </StatusBadge>
          {detail.status !== "active" ? (
            <p>This assignment is historical and read-only.</p>
          ) : null}
          <Card>
            <h3>Tasks</h3>
            <ol>
              {detail.tasks.map((task) => (
                <li key={task.id}>
                  <strong>{task.title}</strong> —{" "}
                  {task.status.replaceAll("_", " ")}
                  {detail.status === "active" ? (
                    <div className="button-row">
                      <Button
                        type="button"
                        disabled={busy || task.status === "completed"}
                        onClick={() => reviewTask(task.id, true)}
                      >
                        Approve task
                      </Button>
                      <Button
                        type="button"
                        disabled={busy || task.status === "completed"}
                        onClick={() => reviewTask(task.id, false)}
                      >
                        Return task
                      </Button>
                    </div>
                  ) : null}
                </li>
              ))}
            </ol>
          </Card>
          <Card>
            <h3>Activation gates</h3>
            <ul>
              {detail.gates.map((gate) => (
                <li key={gate.id}>
                  <strong>{gate.label}</strong>:{" "}
                  <StatusBadge
                    tone={gate.status === "satisfied" ? "success" : "warning"}
                  >
                    {gate.status}
                  </StatusBadge>{" "}
                  ({gate.evidence_kind})
                  {gate.evidence_kind === "manual" &&
                  detail.status === "active" ? (
                    <div className="button-row">
                      {gate.status === "open" ? (
                        <Button
                          type="button"
                          onClick={() => {
                            setGateCode(gate.code);
                            setGateAction("satisfy");
                          }}
                        >
                          Record evidence
                        </Button>
                      ) : (
                        <Button
                          type="button"
                          onClick={() => {
                            setGateCode(gate.code);
                            setGateAction("reopen");
                          }}
                        >
                          Reopen with reason
                        </Button>
                      )}
                    </div>
                  ) : gate.evidence_kind === "derived" ? (
                    <p>
                      Derived from exact assignment evidence; no manual
                      override.
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
            {gateCode && detail.status === "active" ? (
              <form onSubmit={submitGate} aria-busy={busy}>
                <h4>
                  {gateAction === "satisfy" ? "Record evidence" : "Reopen gate"}
                  : {gateCode.replaceAll("_", " ")}
                </h4>
                {gateAction === "satisfy" ? (
                  <>
                    <FormField
                      id="gate-verified-on"
                      label="Verification date (required)"
                    >
                      <input
                        id="gate-verified-on"
                        type="date"
                        value={verifiedOn}
                        onChange={(event) => setVerifiedOn(event.target.value)}
                        required
                      />
                    </FormField>
                    <FormField
                      id="gate-evidence-source"
                      label="Evidence source (required)"
                    >
                      <input
                        id="gate-evidence-source"
                        value={evidenceSource}
                        maxLength={120}
                        onChange={(event) =>
                          setEvidenceSource(event.target.value)
                        }
                        required
                      />
                    </FormField>
                    <FormField
                      id="gate-evidence-reference"
                      label="Non-sensitive evidence reference (required)"
                    >
                      <input
                        id="gate-evidence-reference"
                        value={evidenceReference}
                        maxLength={160}
                        onChange={(event) =>
                          setEvidenceReference(event.target.value)
                        }
                        required
                      />
                    </FormField>
                  </>
                ) : (
                  <FormField
                    id="gate-reopen-reason"
                    label="Correction reason (required)"
                  >
                    <textarea
                      id="gate-reopen-reason"
                      value={reopenReason}
                      maxLength={500}
                      onChange={(event) => setReopenReason(event.target.value)}
                      required
                    />
                  </FormField>
                )}
                <div className="button-row">
                  <Button type="submit" disabled={busy}>
                    {gateAction === "satisfy"
                      ? "Confirm gate evidence"
                      : "Confirm reopen"}
                  </Button>
                  <Button type="button" onClick={() => setGateCode("")}>
                    Cancel
                  </Button>
                </div>
              </form>
            ) : null}
          </Card>
          <Card>
            <h3>Documenso agreement</h3>
            <p>
              Enter only the Documenso document ID. Keeper does not store
              recipient signing links or signed files.
            </p>
            {detail.status === "active" ? (
              <form onSubmit={linkEnvelope} aria-busy={busy}>
                <FormField
                  id="documenso-envelope-id"
                  label={
                    replacementRecordId
                      ? "Replacement Documenso document ID (required)"
                      : "Documenso document ID (required)"
                  }
                >
                  <input
                    id="documenso-envelope-id"
                    value={envelopeId}
                    maxLength={255}
                    onChange={(event) => setEnvelopeId(event.target.value)}
                    required
                  />
                </FormField>
                <Button type="submit" disabled={busy}>
                  {replacementRecordId
                    ? "Link replacement envelope"
                    : "Link Documenso envelope"}
                </Button>
              </form>
            ) : null}
            <ul>
              {detail.esign_envelopes.map((envelope) => (
                <li key={envelope.id}>
                  Documenso {envelope.envelope_id ?? "legacy record"}:{" "}
                  <StatusBadge
                    tone={
                      envelope.status === "completed" ? "success" : "warning"
                    }
                  >
                    {envelope.status}
                  </StatusBadge>
                  {envelope.superseded_at ? " — superseded" : ""}
                  {!envelope.superseded_at && detail.status === "active" ? (
                    <div className="button-row">
                      <Button
                        type="button"
                        disabled={busy}
                        onClick={() => refreshEnvelope(envelope.id)}
                      >
                        Refresh from Documenso
                      </Button>
                      {["rejected", "voided"].includes(envelope.status) ? (
                        <Button
                          type="button"
                          onClick={() => setReplacementRecordId(envelope.id)}
                        >
                          Replace envelope
                        </Button>
                      ) : null}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <h3>Readiness</h3>
            {detail.status === "active" ? (
              <StatusBadge
                tone={detail.activation_ready ? "success" : "warning"}
              >
                {detail.activation_ready
                  ? "All current readiness evidence is satisfied"
                  : "Readiness evidence remains incomplete"}
              </StatusBadge>
            ) : (
              <p>Historical assignment readiness is not evaluated.</p>
            )}
            <p>
              No final activation action exists on this screen or in the API.
            </p>
          </Card>
        </section>
      ) : null}
    </div>
  );
}
