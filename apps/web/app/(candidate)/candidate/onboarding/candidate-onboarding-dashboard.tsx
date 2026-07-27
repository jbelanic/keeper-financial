"use client";

import { useState } from "react";
import {
  Button,
  Card,
  ErrorSummary,
  ProgressChecklist,
  StatusBadge,
} from "@keeper/ui";
import { candidateBrowserJson } from "@/lib/candidate-browser-api";
import type {
  CandidateOnboardingDashboard,
  CandidateOnboardingTaskResponse,
  ActivationGateResponse,
  ControlledDocumentResponse,
  PolicyAcknowledgementResponse,
} from "@/lib/review-onboarding-api";

const TASK_TONE: Record<string, "neutral" | "success" | "warning" | "danger"> =
  {
    completed: "success",
    submitted: "warning",
    rejected: "danger",
    in_progress: "warning",
    required: "neutral",
  };

export function CandidateOnboardingDashboardView({
  dashboard,
}: {
  dashboard: CandidateOnboardingDashboard;
}) {
  const [tasks, setTasks] = useState<CandidateOnboardingTaskResponse[]>(
    dashboard.tasks,
  );
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [acks, setAcks] = useState<PolicyAcknowledgementResponse[]>(
    dashboard.acknowledgements,
  );
  const [evidenceText, setEvidenceText] = useState("");
  const [ackWording, setAckWording] = useState("");
  const assignmentCompleted = dashboard.assignment?.status === "completed";
  const currentEnvelope = dashboard.esign_envelopes.find(
    (envelope) => !envelope.superseded_at,
  );

  const requiredTasks = tasks.filter((task) => task.status !== "completed");
  const completedCount = tasks.length - requiredTasks.length;

  async function submitEvidence(taskId: string) {
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Submitting task evidence…");
    try {
      const response =
        await candidateBrowserJson<CandidateOnboardingTaskResponse>(
          `/api/v1/candidate/onboarding/tasks/${taskId}/evidence`,
          {
            method: "POST",
            body: JSON.stringify({ evidence: evidenceText.trim() }),
            headers: { "Content-Type": "application/json" },
          },
        );
      setTasks((items) =>
        items.map((item) => (item.id === taskId ? response : item)),
      );
      setEvidenceText("");
      setNotice("Task evidence submitted for review.");
    } catch {
      setErrors(["Evidence could not be submitted."]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function acknowledge(documentVersionId: string) {
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Recording acknowledgement…");
    try {
      const response =
        await candidateBrowserJson<PolicyAcknowledgementResponse>(
          "/api/v1/candidate/onboarding/acknowledgements",
          {
            method: "POST",
            body: JSON.stringify({
              document_version_id: documentVersionId,
              wording: ackWording.trim(),
            }),
            headers: { "Content-Type": "application/json" },
          },
        );
      setAcks((items) => [...items, response]);
      setAckWording("");
      setNotice("Policy acknowledged.");
    } catch {
      setErrors(["Acknowledgement could not be recorded."]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="candidate-onboarding">
      <p role="status" aria-live="polite">
        {notice}
      </p>
      <ErrorSummary errors={errors} />

      <Card>
        <h2>Onboarding status</h2>
        {assignmentCompleted ? (
          <p>
            <StatusBadge tone="success">Onboarding completed</StatusBadge> Your
            completed onboarding evidence remains available here as read-only
            history.
          </p>
        ) : dashboard.activation_ready ? (
          <p>
            <StatusBadge tone="success">
              Onboarding requirements complete
            </StatusBadge>{" "}
            Required assigned tasks, policies, and gates are complete. This does
            not perform final activation.
          </p>
        ) : (
          <p>
            <StatusBadge tone="warning">In progress</StatusBadge> Complete the
            required assigned tasks, policies, and gates below. Final activation
            is not performed by this portal.
          </p>
        )}
      </Card>

      <section aria-labelledby="tasks-heading">
        <h2 id="tasks-heading">Your tasks</h2>
        {tasks.length === 0 ? (
          <p>No onboarding tasks have been assigned yet.</p>
        ) : (
          <ul className="grid-2">
            {tasks.map((task) => (
              <li key={task.id}>
                <Card>
                  <h3>Task</h3>
                  <p>
                    Status:{" "}
                    <StatusBadge tone={TASK_TONE[task.status] ?? "neutral"}>
                      {task.status.replace(/_/g, " ")}
                    </StatusBadge>
                  </p>
                  {task.due_at ? <p>Due: {task.due_at}</p> : null}
                  {task.evidence ? <p>Evidence: {task.evidence}</p> : null}
                  {!assignmentCompleted &&
                  (task.status === "required" ||
                    task.status === "in_progress" ||
                    task.status === "rejected") ? (
                    <div>
                      <label htmlFor={`evidence-${task.id}`}>
                        Evidence / notes
                      </label>
                      <textarea
                        id={`evidence-${task.id}`}
                        value={evidenceText}
                        maxLength={2000}
                        onChange={(event) =>
                          setEvidenceText(event.target.value)
                        }
                      />
                      <div className="button-row">
                        <Button
                          type="button"
                          disabled={busy || !evidenceText.trim()}
                          onClick={() => submitEvidence(task.id)}
                        >
                          Submit evidence
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="gates-heading">
        <h2 id="gates-heading">Other requirements</h2>
        <GateList gates={dashboard.gates} />
      </section>

      <section aria-labelledby="documents-heading">
        <h2 id="documents-heading">Documents and policies</h2>
        {dashboard.documents.length === 0 ? (
          <p>No controlled documents are assigned to you.</p>
        ) : (
          <ul>
            {dashboard.documents.map((doc: ControlledDocumentResponse) => {
              const acked = acks.some(
                (ack) =>
                  doc.current_version &&
                  ack.document_version_id === doc.current_version.id,
              );
              return (
                <li key={doc.id}>
                  <Card>
                    <h3>{doc.title}</h3>
                    <p>{doc.description}</p>
                    {doc.requires_acknowledgement ? (
                      acked || assignmentCompleted ? (
                        <p>
                          <StatusBadge tone="success">Acknowledged</StatusBadge>
                        </p>
                      ) : (
                        <div>
                          <label htmlFor={`ack-${doc.id}`}>
                            Acknowledgement wording
                          </label>
                          <textarea
                            id={`ack-${doc.id}`}
                            value={ackWording}
                            maxLength={2000}
                            onChange={(event) =>
                              setAckWording(event.target.value)
                            }
                          />
                          <div className="button-row">
                            <Button
                              type="button"
                              disabled={busy || !ackWording.trim()}
                              onClick={() =>
                                doc.current_version &&
                                acknowledge(doc.current_version.id)
                              }
                            >
                              Acknowledge
                            </Button>
                          </div>
                        </div>
                      )
                    ) : null}
                  </Card>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section aria-labelledby="esign-heading">
        <h2 id="esign-heading">External signing</h2>
        {!currentEnvelope ? (
          <p>The contractor agreement has not been sent yet.</p>
        ) : (
          <Card>
            <p>
              Agreement status:{" "}
              <StatusBadge
                tone={
                  currentEnvelope.status === "completed" ? "success" : "warning"
                }
              >
                {currentEnvelope.status === "sent"
                  ? "sent / waiting for signature"
                  : currentEnvelope.status}
              </StatusBadge>
            </p>
            {!assignmentCompleted &&
            currentEnvelope.status === "sent" &&
            currentEnvelope.envelope_url ? (
              <p>
                <a
                  href={currentEnvelope.envelope_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Review and sign contractor agreement
                </a>
              </p>
            ) : null}
            {!assignmentCompleted && currentEnvelope.status === "sent" ? (
              <p>
                After signing, an administrator may need to refresh the provider
                status.
              </p>
            ) : null}
          </Card>
        )}
      </section>

      {tasks.length > 0 ? (
        <section aria-labelledby="progress-heading">
          <h2 id="progress-heading">Progress</h2>
          <ProgressChecklist
            items={[
              { label: "Tasks completed", complete: completedCount > 0 },
              {
                label: "All required tasks completed",
                complete: requiredTasks.length === 0,
              },
              {
                label: "Required policies acknowledged",
                complete: dashboard.documents
                  .filter((d) => d.requires_acknowledgement)
                  .every((d) =>
                    acks.some(
                      (a) =>
                        d.current_version &&
                        a.document_version_id === d.current_version.id,
                    ),
                  ),
              },
              {
                label: "Onboarding requirements complete",
                complete: dashboard.activation_ready,
              },
            ]}
          />
        </section>
      ) : null}
    </div>
  );
}

function GateList({ gates }: { gates: ActivationGateResponse[] }) {
  if (gates.length === 0)
    return <p>No other requirements are configured for your onboarding.</p>;
  return (
    <ul>
      {gates.map((gate) => (
        <li key={gate.id}>
          <Card>
            <h3>{gate.label}</h3>
            <p>
              Status:{" "}
              <StatusBadge
                tone={gate.status === "satisfied" ? "success" : "warning"}
              >
                {gate.status}
              </StatusBadge>
            </p>
          </Card>
        </li>
      ))}
    </ul>
  );
}
