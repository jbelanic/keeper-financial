"use client";

import { useRef, useState } from "react";
import {
  Button,
  Card,
  DataTable,
  ErrorSummary,
  StatusBadge,
  ConfirmationDialog,
} from "@keeper/ui";
import { adminBrowserRequest } from "@/lib/admin-browser-api";
import type {
  CandidateQueueResponse,
  CandidateReviewSummary,
  CandidateDetailResponse,
  CandidateDecisionRequest,
  InterviewStatusUpdate,
  InformationRequestCreate,
  InformationRequestResponse,
} from "@/lib/review-onboarding-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

const STATUS_TONE: Record<
  string,
  "neutral" | "success" | "warning" | "danger"
> = {
  under_review: "warning",
  interview: "warning",
  conditionally_selected: "success",
  more_information_required: "warning",
  declined: "danger",
  withdrawn: "danger",
};
const INFORMATION_REQUEST_STATUSES = new Set(["under_review", "interview"]);
const INTERVIEW_STATUSES = new Set([
  "under_review",
  "more_information_required",
  "interview",
]);

class ReviewRequestError extends Error {
  constructor(public readonly status: number) {
    super(`review request failed (${status})`);
  }
}

export function CandidateReviewPipeline({
  initialQueue,
  requester = adminBrowserRequest,
}: {
  initialQueue: CandidateQueueResponse;
  requester?: Requester;
}) {
  const [queue, setQueue] = useState(initialQueue);
  const [selected, setSelected] = useState<CandidateReviewSummary | null>(null);
  const [detail, setDetail] = useState<CandidateDetailResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  const [decisionTarget, setDecisionTarget] =
    useState<CandidateReviewSummary | null>(null);
  const [decision, setDecision] = useState<"declined" | "withdrawn">(
    "declined",
  );
  const [reason, setReason] = useState("");
  const dialogRef = useRef<HTMLDialogElement | null>(null);

  async function openDetail(candidate: CandidateReviewSummary) {
    setSelected(candidate);
    setDetail(null);
    setBusy(true);
    setErrors([]);
    try {
      const response = await requester(
        `/api/v1/admin/candidates/${candidate.candidate_id}?application_id=${candidate.application_id}`,
      );
      if (!response.ok) throw new Error("detail unavailable");
      setDetail((await response.json()) as CandidateDetailResponse);
    } catch {
      setErrors(["Could not load candidate detail."]);
    } finally {
      setBusy(false);
    }
  }

  async function postJson<T>(path: string, body: unknown): Promise<T> {
    const response = await requester(path, {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) throw new ReviewRequestError(response.status);
    return (await response.json()) as T;
  }

  async function saveInterview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selected ||
      !detail ||
      detail.application_id !== selected.application_id ||
      !INTERVIEW_STATUSES.has(detail.status)
    )
      return;
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Recording interview status…");
    const form = new FormData(event.currentTarget);
    const payload: InterviewStatusUpdate = {
      application_id: selected.application_id,
      interview_status: String(
        form.get("interview_status") ?? "scheduled",
      ) as InterviewStatusUpdate["interview_status"],
      notes: String(form.get("notes") ?? "") || null,
    };
    try {
      const updated = await postJson<CandidateDetailResponse>(
        `/api/v1/admin/candidates/${selected.candidate_id}/interview`,
        payload,
      );
      setDetail(updated);
      setNotice("Interview status recorded.");
    } catch {
      setErrors(["Interview status could not be recorded."]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function requestInfo(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !selected ||
      !detail ||
      detail.application_id !== selected.application_id
    )
      return;
    if (busy) return;
    if (!INFORMATION_REQUEST_STATUSES.has(detail.status)) {
      setErrors([
        "Begin review for this selected application before requesting information.",
      ]);
      return;
    }
    setBusy(true);
    setErrors([]);
    setNotice("Sending information request…");
    const form = new FormData(event.currentTarget);
    const payload: InformationRequestCreate = {
      application_id: selected.application_id,
      message: String(form.get("message") ?? "").trim(),
    };
    try {
      await postJson<InformationRequestResponse>(
        `/api/v1/admin/candidates/${selected.candidate_id}/information-requests`,
        payload,
      );
      setDetail((current) =>
        current?.application_id === selected.application_id
          ? { ...current, status: "more_information_required" }
          : current,
      );
      setQueue((current) => ({
        ...current,
        items: current.items.map((item) =>
          item.application_id === selected.application_id
            ? { ...item, status: "more_information_required" }
            : item,
        ),
      }));
      setNotice("Information request sent.");
    } catch (error) {
      setErrors([
        error instanceof ReviewRequestError && error.status === 409
          ? "Information can be requested only while the selected application is under review or in interview."
          : "The information request could not be sent for the selected application.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function recordProgressDecision(
    target: "under_review" | "conditionally_selected",
  ) {
    if (!selected || busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Recording application decision…");
    const payload: CandidateDecisionRequest = {
      application_id: selected.application_id,
      decision: target,
      reason: null,
    };
    try {
      const updated = await postJson<CandidateDetailResponse>(
        `/api/v1/admin/candidates/${selected.candidate_id}/decision`,
        payload,
      );
      setDetail(updated);
      setQueue((previous) => ({
        ...previous,
        items: previous.items.map((item) =>
          item.application_id === selected.application_id
            ? { ...item, status: updated.status }
            : item,
        ),
      }));
      setNotice(
        target === "under_review"
          ? "Application moved into review."
          : "Application conditionally selected.",
      );
    } catch {
      setErrors([
        "The application transition was rejected for its current status.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function confirmDecision() {
    if (!decisionTarget) return;
    setBusy(true);
    setErrors([]);
    setNotice("Recording decision…");
    const payload: CandidateDecisionRequest = {
      application_id: decisionTarget.application_id,
      decision,
      reason: reason.trim() || null,
    };
    try {
      const updated = await postJson<CandidateDetailResponse>(
        `/api/v1/admin/candidates/${decisionTarget.candidate_id}/decision`,
        payload,
      );
      setQueue((prev) => ({
        ...prev,
        items: prev.items.filter(
          (item) => item.application_id !== decisionTarget.application_id,
        ),
        total: Math.max(0, prev.total - 1),
      }));
      setDetail(updated);
      setSelected(null);
      setDecisionTarget(null);
      setReason("");
      setNotice(
        decision === "declined"
          ? "Candidate declined and recorded."
          : "Candidate withdrawal recorded.",
      );
    } catch {
      setErrors([
        "The decision was rejected. Decline/withdraw requires a reason and a valid current status.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="review-pipeline">
      <p role="status" aria-live="polite">
        {notice}
      </p>
      <ErrorSummary errors={errors} />

      <section aria-labelledby="queue-heading">
        <h2 id="queue-heading">Review queue ({queue.total})</h2>
        {queue.items.length === 0 ? (
          <p>No candidates are currently awaiting review.</p>
        ) : (
          <DataTable
            caption="Candidates awaiting review"
            headers={["Name", "Opportunity", "Status", "Interview", "Actions"]}
            rows={queue.items.map((item) => [
              <span key="name">
                {item.given_name ?? "—"} {item.family_name ?? ""}
                <br />
                <span className="visually-hidden">email </span>
                <span className="muted">{item.email}</span>
              </span>,
              <span key="opportunity">
                {item.source_posting_title}
                <br />
                <span className="muted">Attempt {item.attempt_number}</span>
              </span>,
              <StatusBadge
                key="status"
                tone={STATUS_TONE[item.status] ?? "neutral"}
              >
                {item.status.replace(/_/g, " ")}
              </StatusBadge>,
              <span key="interview">
                {item.interview_status
                  ? item.interview_status.replace(/_/g, " ")
                  : "—"}
              </span>,
              <Button
                key="actions"
                type="button"
                onClick={() => openDetail(item)}
                disabled={busy}
                aria-label={`Review ${item.given_name ?? "candidate"} for ${item.source_posting_title}, attempt ${item.attempt_number}`}
              >
                Review
              </Button>,
            ])}
          />
        )}
      </section>

      {selected && detail ? (
        <Card aria-labelledby="detail-heading">
          <h2 id="detail-heading">
            {detail.given_name ?? "Candidate"} {detail.family_name ?? ""}
          </h2>
          <p>
            Opportunity: <strong>{detail.source_posting_title}</strong> ·
            Attempt {detail.attempt_number}
          </p>
          <p>
            Status:{" "}
            <StatusBadge>{detail.status.replace(/_/g, " ")}</StatusBadge>
          </p>
          {detail.interview_status ? (
            <p>
              Interview: {detail.interview_status.replace(/_/g, " ")}
              {detail.interview_notes ? ` — ${detail.interview_notes}` : ""}
            </p>
          ) : null}

          <form className="card" onSubmit={saveInterview} aria-busy={busy}>
            <h3>Record interview status</h3>
            <fieldset disabled={busy || !INTERVIEW_STATUSES.has(detail.status)}>
              <legend className="visually-hidden">
                Selected application interview
              </legend>
              <label htmlFor="interview-status">Interview status</label>
              <select
                id="interview-status"
                name="interview_status"
                defaultValue="scheduled"
              >
                <option value="scheduled">Scheduled</option>
                <option value="completed">Completed</option>
                <option value="cancelled">Cancelled</option>
                <option value="no_show">No show</option>
              </select>
              <label htmlFor="interview-notes">Notes (plain text)</label>
              <textarea id="interview-notes" name="notes" maxLength={1000} />
              <div className="button-row">
                <Button
                  type="submit"
                  disabled={busy || !INTERVIEW_STATUSES.has(detail.status)}
                >
                  Save interview status
                </Button>
              </div>
            </fieldset>
            {!INTERVIEW_STATUSES.has(detail.status) ? (
              <p className="notice">
                Begin review for this selected application before recording an
                interview.
              </p>
            ) : null}
          </form>

          <form className="card" onSubmit={requestInfo} aria-busy={busy}>
            <h3>Request information</h3>
            <p>
              Selected opportunity:{" "}
              <strong>{detail.source_posting_title}</strong>, attempt{" "}
              {detail.attempt_number}.
            </p>
            <fieldset
              disabled={
                busy || !INFORMATION_REQUEST_STATUSES.has(detail.status)
              }
            >
              <legend className="visually-hidden">
                Selected application information request
              </legend>
              <label htmlFor="info-message">Message to candidate</label>
              <textarea
                id="info-message"
                name="message"
                maxLength={2000}
                required
              />
              <div className="button-row">
                <Button
                  type="submit"
                  disabled={
                    busy || !INFORMATION_REQUEST_STATUSES.has(detail.status)
                  }
                >
                  Send request
                </Button>
              </div>
            </fieldset>
            {!INFORMATION_REQUEST_STATUSES.has(detail.status) ? (
              <p className="notice">
                Information can be requested only while this selected
                application is under review or in interview. Begin review first
                when it is newly submitted.
              </p>
            ) : null}
          </form>

          <div className="button-row">
            {detail.status === "application_submitted" ||
            detail.status === "more_information_required" ? (
              <Button
                type="button"
                disabled={busy}
                onClick={() => recordProgressDecision("under_review")}
              >
                Begin review
              </Button>
            ) : null}
            {detail.status === "under_review" ||
            detail.status === "interview" ? (
              <Button
                type="button"
                disabled={busy}
                onClick={() => recordProgressDecision("conditionally_selected")}
              >
                Conditionally select application
              </Button>
            ) : null}
            <Button
              type="button"
              className="button-danger"
              disabled={busy}
              onClick={() => {
                setDecision("declined");
                setReason("");
                setDecisionTarget(selected);
              }}
            >
              Decline candidate
            </Button>
            <Button
              type="button"
              disabled={busy}
              onClick={() => {
                setDecision("withdrawn");
                setReason("");
                setDecisionTarget(selected);
              }}
            >
              Mark withdrawn
            </Button>
          </div>
        </Card>
      ) : selected ? (
        <p role="status">Loading candidate detail…</p>
      ) : (
        <Card>
          <h2>Application actions</h2>
          <p>
            Select an exact opportunity and application attempt from the review
            queue.
          </p>
          <Button type="button" disabled>
            Send request
          </Button>
        </Card>
      )}

      <ConfirmationDialog
        title={
          decision === "declined"
            ? "Decline this candidate?"
            : "Mark candidate as withdrawn?"
        }
        open={decisionTarget !== null}
        onCancel={() => setDecisionTarget(null)}
        onConfirm={confirmDecision}
        dialogRef={dialogRef}
        busy={busy}
      >
        <p>
          A reason is recorded with the actor and timestamp. This is a
          controlled, audited status change.
        </p>
        <label htmlFor="decision-reason">
          Reason <span aria-hidden="true">*</span>
        </label>
        <textarea
          id="decision-reason"
          value={reason}
          maxLength={1000}
          onChange={(event) => setReason(event.target.value)}
          required
        />
      </ConfirmationDialog>
    </div>
  );
}
