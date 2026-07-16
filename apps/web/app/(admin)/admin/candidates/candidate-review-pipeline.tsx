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
        `/api/v1/admin/candidates/${candidate.candidate_id}`,
      );
      if (!response.ok) throw new Error("detail unavailable");
      setDetail((await response.json()) as CandidateDetailResponse);
    } catch {
      setErrors(["Could not load candidate detail."]);
    } finally {
      setBusy(false);
    }
  }

  async function postJson(path: string, body: unknown) {
    const response = await requester(path, {
      method: "POST",
      body: JSON.stringify(body),
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) throw new Error("request rejected");
    return (await response.json()) as CandidateDetailResponse;
  }

  async function saveInterview(event: React.FormEvent<HTMLFormElement>) {
    if (!selected) return;
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Recording interview status…");
    const form = new FormData(event.currentTarget);
    const payload: InterviewStatusUpdate = {
      interview_status: String(
        form.get("interview_status") ?? "scheduled",
      ) as InterviewStatusUpdate["interview_status"],
      notes: String(form.get("notes") ?? "") || null,
    };
    try {
      const updated = await postJson(
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
    if (!selected) return;
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Sending information request…");
    const form = new FormData(event.currentTarget);
    const payload: InformationRequestCreate = {
      message: String(form.get("message") ?? "").trim(),
    };
    try {
      await postJson(
        `/api/v1/admin/candidates/${selected.candidate_id}/information-requests`,
        payload,
      );
      setNotice("Information request sent.");
    } catch {
      setErrors(["The information request could not be sent."]);
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
      decision,
      reason: reason.trim() || null,
    };
    try {
      const updated = await postJson(
        `/api/v1/admin/candidates/${decisionTarget.candidate_id}/decision`,
        payload,
      );
      setQueue((prev) => ({
        ...prev,
        items: prev.items.filter(
          (item) => item.candidate_id !== decisionTarget.candidate_id,
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
            headers={["Name", "Status", "Interview", "Actions"]}
            rows={queue.items.map((item) => [
              <span key="name">
                {item.given_name ?? "—"} {item.family_name ?? ""}
                <br />
                <span className="visually-hidden">email </span>
                <span className="muted">{item.email}</span>
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
                aria-label={`Review ${item.given_name ?? "candidate"}`}
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
              <Button type="submit" disabled={busy}>
                Save interview status
              </Button>
            </div>
          </form>

          <form className="card" onSubmit={requestInfo} aria-busy={busy}>
            <h3>Request information</h3>
            <label htmlFor="info-message">Message to candidate</label>
            <textarea
              id="info-message"
              name="message"
              maxLength={1000}
              required
            />
            <div className="button-row">
              <Button type="submit" disabled={busy}>
                Send request
              </Button>
            </div>
          </form>

          <div className="button-row">
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
      ) : null}

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
