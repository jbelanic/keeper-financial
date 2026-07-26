"use client";

import { useState } from "react";
import { Button, Card, DataTable, ErrorSummary, StatusBadge } from "@keeper/ui";
import type { EligibleAgent } from "@/lib/agent-api";
import { adminBrowserRequest } from "@/lib/admin-browser-api";
import type {
  BorrowerDocumentListResponse,
  BorrowerInternalProjection,
  BorrowerReviewQueueItem,
  BorrowerReviewQueueResponse,
} from "@/lib/borrower-review-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

type SelectedReview = {
  queueItem: BorrowerReviewQueueItem;
  detail: BorrowerInternalProjection;
  documents: BorrowerDocumentListResponse;
};

const REVEAL_REASONS = [
  "credit_review",
  "borrower_identity_review",
  "document_reconciliation",
  "supervisory_review",
];

function formatJson(value: Record<string, unknown> | null) {
  if (!value) return "None recorded.";
  return JSON.stringify(value, null, 2);
}

export function BorrowerReviewConsole({
  initialQueue,
  eligibleAgents,
  requester = adminBrowserRequest,
}: {
  initialQueue: BorrowerReviewQueueResponse;
  eligibleAgents: EligibleAgent[];
  requester?: Requester;
}) {
  const [queue, setQueue] = useState(initialQueue);
  const [selected, setSelected] = useState<SelectedReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);
  const [revealedSin, setRevealedSin] = useState("");

  async function loadReview(item: BorrowerReviewQueueItem) {
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Loading borrower application...");
    setRevealedSin("");
    try {
      const [detailResponse, documentResponse] = await Promise.all([
        requester(
          `/api/v1/borrower-applications/${item.application_id}/internal`,
        ),
        requester(
          `/api/v1/borrower-applications/${item.application_id}/documents`,
        ),
      ]);
      if (!detailResponse.ok || !documentResponse.ok) {
        throw new Error("review detail unavailable");
      }
      setSelected({
        queueItem: item,
        detail: (await detailResponse.json()) as BorrowerInternalProjection,
        documents:
          (await documentResponse.json()) as BorrowerDocumentListResponse,
      });
      setNotice("Borrower application loaded.");
    } catch {
      setErrors(["The selected borrower application could not be loaded."]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function assign(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || busy) return;
    const form = new FormData(event.currentTarget);
    const agentUserId = String(form.get("agent_user_id") ?? "");
    const reasonCategory = String(form.get("reason_category") ?? "");
    const reasonDetail = String(form.get("reason_detail") ?? "").trim();
    if (!agentUserId || !reasonCategory) {
      setErrors(["Select an active agent and assignment reason."]);
      return;
    }
    setBusy(true);
    setErrors([]);
    setNotice("Recording assignment...");
    try {
      const response = await requester(
        `/api/v1/borrower-applications/${selected.queueItem.application_id}/assignment`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            agent_user_id: agentUserId,
            reason_category: reasonCategory,
            reason_detail: reasonDetail || null,
          }),
        },
      );
      if (!response.ok) throw new Error("assignment rejected");
      const result = (await response.json()) as {
        lifecycle_status: string;
        assigned_agent_id: string;
        assigned_at: string | null;
      };
      const agent = eligibleAgents.find(
        (item) => item.user_id === result.assigned_agent_id,
      );
      setQueue((current) => ({
        ...current,
        items: current.items.map((item) =>
          item.application_id === selected.queueItem.application_id
            ? {
                ...item,
                lifecycle_status: result.lifecycle_status,
                assigned_agent_id: result.assigned_agent_id,
                assigned_agent_name: agent?.display_name ?? null,
                assigned_agent_email: agent?.email ?? null,
              }
            : item,
        ),
      }));
      setSelected((current) =>
        current
          ? {
              ...current,
              queueItem: {
                ...current.queueItem,
                lifecycle_status: result.lifecycle_status,
                assigned_agent_id: result.assigned_agent_id,
                assigned_agent_name: agent?.display_name ?? null,
                assigned_agent_email: agent?.email ?? null,
              },
              detail: {
                ...current.detail,
                lifecycle_status: result.lifecycle_status,
              },
            }
          : current,
      );
      setNotice("Assignment recorded.");
    } catch {
      setErrors([
        "Assignment was rejected. Confirm the target agent is active and the application remains assignable.",
      ]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function revealSin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || busy) return;
    const reason = String(
      new FormData(event.currentTarget).get("reason") ?? "",
    );
    setBusy(true);
    setErrors([]);
    setNotice("Revealing SIN for this session...");
    setRevealedSin("");
    try {
      const response = await requester(
        `/api/v1/borrower-applications/${selected.queueItem.application_id}/sin/reveal`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ reason_category: reason }),
        },
      );
      if (!response.ok) throw new Error("reveal rejected");
      const result = (await response.json()) as { sin: string };
      setRevealedSin(result.sin);
      setNotice("SIN revealed for this authorized request.");
    } catch {
      setErrors(["SIN reveal was rejected for this application and reason."]);
      setNotice("");
    } finally {
      setBusy(false);
    }
  }

  async function downloadDocument(documentId: string) {
    if (!selected || busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Preparing document download...");
    try {
      const response = await requester(
        `/api/v1/borrower-applications/${selected.queueItem.application_id}/documents/${documentId}/download`,
      );
      if (!response.ok) throw new Error("download rejected");
      const blob = await response.blob();
      const disposition = response.headers.get("content-disposition") ?? "";
      const filenameMatch = /filename="([^"]+)"/.exec(disposition);
      const filename = filenameMatch?.[1] ?? "borrower-document";
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      anchor.rel = "noopener noreferrer";
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setNotice("Document download prepared.");
    } catch {
      setErrors(["Document download was rejected for this reviewer."]);
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

      <section aria-labelledby="borrower-queue-heading">
        <h2 id="borrower-queue-heading">
          Submitted applications ({queue.total})
        </h2>
        {queue.items.length === 0 ? (
          <p>
            No submitted borrower applications are currently awaiting review.
          </p>
        ) : (
          <DataTable
            caption="Submitted borrower applications"
            headers={[
              "Application",
              "Status",
              "Assigned agent",
              "Submitted",
              "Action",
            ]}
            rows={queue.items.map((item) => [
              <code key="id">{item.application_id}</code>,
              <StatusBadge key="status" tone="warning">
                {item.lifecycle_status.replace(/_/g, " ")}
              </StatusBadge>,
              <span key="agent">
                {item.assigned_agent_name ?? "Unassigned"}
                {item.assigned_agent_email ? (
                  <>
                    <br />
                    <span className="muted">{item.assigned_agent_email}</span>
                  </>
                ) : null}
              </span>,
              item.submitted_at
                ? new Date(item.submitted_at).toLocaleString()
                : "Pending",
              <Button
                key="action"
                type="button"
                onClick={() => loadReview(item)}
                disabled={busy}
              >
                Review
              </Button>,
            ])}
          />
        )}
      </section>

      {selected ? (
        <Card aria-labelledby="borrower-detail-heading">
          <h2 id="borrower-detail-heading">Application detail</h2>
          <p>
            Status:{" "}
            <StatusBadge>
              {selected.detail.lifecycle_status.replace(/_/g, " ")}
            </StatusBadge>
          </p>

          <form onSubmit={assign} aria-busy={busy}>
            <h3>Assign agent</h3>
            <label htmlFor="agent-user-id">Active mortgage agent</label>
            <select
              id="agent-user-id"
              name="agent_user_id"
              defaultValue={selected.queueItem.assigned_agent_id ?? ""}
              required
            >
              <option value="">Select an active agent</option>
              {eligibleAgents.map((agent) => (
                <option key={agent.user_id} value={agent.user_id}>
                  {agent.display_name} - {agent.email}
                </option>
              ))}
            </select>
            <label htmlFor="assignment-reason">Reason</label>
            <select id="assignment-reason" name="reason_category" required>
              <option value="initial_assignment">Initial assignment</option>
              <option value="reassignment">Reassignment</option>
              <option value="workload">Workload</option>
              <option value="coverage">Coverage</option>
              <option value="conflict">Conflict</option>
              <option value="correction">Correction</option>
            </select>
            <label htmlFor="assignment-detail">Reason detail</label>
            <textarea
              id="assignment-detail"
              name="reason_detail"
              maxLength={512}
            />
            <div className="button-row">
              <Button type="submit" disabled={busy}>
                Save assignment
              </Button>
            </div>
          </form>

          <section aria-labelledby="borrower-primary-heading">
            <h3 id="borrower-primary-heading">Primary borrower</h3>
            {selected.detail.primary_borrower ? (
              <dl>
                <dt>Name</dt>
                <dd>
                  {selected.detail.primary_borrower.first_name}{" "}
                  {selected.detail.primary_borrower.last_name}
                </dd>
                <dt>Email</dt>
                <dd>{selected.detail.primary_borrower.email}</dd>
                <dt>Phone</dt>
                <dd>{selected.detail.primary_borrower.phone}</dd>
                <dt>SIN</dt>
                <dd>
                  {selected.detail.primary_borrower.sin?.display ?? "Masked"}
                </dd>
              </dl>
            ) : (
              <p>No primary borrower projection is available.</p>
            )}
          </section>

          <section aria-labelledby="borrower-request-heading">
            <h3 id="borrower-request-heading">Mortgage request</h3>
            <pre>{formatJson(selected.detail.mortgage_request ?? null)}</pre>
          </section>

          <section aria-labelledby="borrower-documents-heading">
            <h3 id="borrower-documents-heading">
              Supporting documents ({selected.documents.total})
            </h3>
            {selected.documents.items.length === 0 ? (
              <p>No supporting documents are attached.</p>
            ) : (
              <DataTable
                caption="Borrower supporting documents"
                headers={["Filename", "Type", "Size", "Download"]}
                rows={selected.documents.items.map((document) => [
                  document.filename,
                  document.mime_type,
                  `${Math.round(document.size_bytes / 1024)} KB`,
                  <Button
                    key="download"
                    type="button"
                    onClick={() => downloadDocument(document.document_id)}
                    disabled={busy}
                  >
                    Download
                  </Button>,
                ])}
              />
            )}
          </section>

          <form onSubmit={revealSin} aria-busy={busy}>
            <h3>Reveal SIN</h3>
            <label htmlFor="sin-reason">Reason</label>
            <select id="sin-reason" name="reason" required>
              {REVEAL_REASONS.map((reason) => (
                <option key={reason} value={reason}>
                  {reason.replace(/_/g, " ")}
                </option>
              ))}
            </select>
            <div className="button-row">
              <Button type="submit" disabled={busy}>
                Reveal SIN
              </Button>
            </div>
            {revealedSin ? (
              <p>
                Revealed SIN: <strong>{revealedSin}</strong>
              </p>
            ) : null}
          </form>
        </Card>
      ) : null}
    </div>
  );
}
