"use client";

import { useState } from "react";
import { Button, Card, DataTable, ErrorSummary, StatusBadge } from "@keeper/ui";
import type {
  BorrowerAgentProjection,
  BorrowerDocumentListResponse,
  BorrowerReviewQueueItem,
  BorrowerReviewQueueResponse,
} from "@/lib/borrower-review-api";
import { agentBrowserRequest } from "@/lib/agent-browser-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

type SelectedReview = {
  queueItem: BorrowerReviewQueueItem;
  detail: BorrowerAgentProjection;
  documents: BorrowerDocumentListResponse;
};

function formatJson(value: unknown) {
  if (value === null || value === undefined) return "None recorded.";
  return JSON.stringify(value, null, 2);
}

function BorrowerInfo({
  label,
  info,
}: {
  label: string;
  info: NonNullable<BorrowerAgentProjection["primary_borrower"]>;
}) {
  return (
    <section aria-labelledby={`${label}-heading`}>
      <h3 id={`${label}-heading`}>{label}</h3>
      <dl>
        <dt>Name</dt>
        <dd>
          {info.first_name} {info.last_name}
        </dd>
        <dt>Email</dt>
        <dd>{info.email}</dd>
        <dt>Phone</dt>
        <dd>{info.phone}</dd>
        <dt>Date of birth</dt>
        <dd>{String(info.date_of_birth)}</dd>
        <dt>SIN</dt>
        <dd>{info.sin ? info.sin : "Not provided"}</dd>
        <dt>Marital status</dt>
        <dd>{info.marital_status}</dd>
        <dt>Number of dependants</dt>
        <dd>{info.number_of_dependants}</dd>
        {info.relationship_to_primary ? (
          <>
            <dt>Relationship to primary</dt>
            <dd>{info.relationship_to_primary}</dd>
          </>
        ) : null}
      </dl>
      <h4>Current address</h4>
      <pre>{formatJson(info.current_address)}</pre>
      <h4>Employment</h4>
      <pre>{formatJson(info.employment)}</pre>
    </section>
  );
}

export function AgentAssignedConsole({
  initialQueue,
  requester = agentBrowserRequest,
}: {
  initialQueue: BorrowerReviewQueueResponse;
  requester?: Requester;
}) {
  const [selected, setSelected] = useState<SelectedReview | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [errors, setErrors] = useState<string[]>([]);

  async function loadReview(item: BorrowerReviewQueueItem) {
    if (busy) return;
    setBusy(true);
    setErrors([]);
    setNotice("Loading assigned application...");
    try {
      const [detailResponse, documentResponse] = await Promise.all([
        requester(`/api/v1/borrower-applications/${item.application_id}/agent`),
        requester(
          `/api/v1/borrower-applications/${item.application_id}/documents`,
        ),
      ]);
      if (!detailResponse.ok || !documentResponse.ok) {
        throw new Error("detail unavailable");
      }
      setSelected({
        queueItem: item,
        detail: (await detailResponse.json()) as BorrowerAgentProjection,
        documents:
          (await documentResponse.json()) as BorrowerDocumentListResponse,
      });
      setNotice("Application loaded.");
    } catch {
      setErrors(["The assigned application could not be loaded."]);
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
      setErrors(["Document download was rejected."]);
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

      <section aria-labelledby="agent-queue-heading">
        <h2 id="agent-queue-heading">
          Assigned applications ({initialQueue.total})
        </h2>
        {initialQueue.items.length === 0 ? (
          <p>No borrower applications are currently assigned to you.</p>
        ) : (
          <DataTable
            caption="Assigned borrower applications"
            headers={["Application", "Status", "Submitted", "Action"]}
            rows={initialQueue.items.map((item) => [
              <code key="id">{item.application_id}</code>,
              <StatusBadge key="status" tone="warning">
                {item.lifecycle_status.replace(/_/g, " ")}
              </StatusBadge>,
              item.submitted_at
                ? new Date(item.submitted_at).toLocaleString()
                : "Pending",
              <Button
                key="action"
                type="button"
                onClick={() => loadReview(item)}
                disabled={busy}
              >
                Open
              </Button>,
            ])}
          />
        )}
      </section>

      {selected ? (
        <Card aria-labelledby="agent-detail-heading">
          <h2 id="agent-detail-heading">Application detail</h2>
          <p>
            Status:{" "}
            <StatusBadge>
              {selected.detail.lifecycle_status.replace(/_/g, " ")}
            </StatusBadge>
          </p>

          {selected.detail.primary_borrower ? (
            <BorrowerInfo
              label="Primary borrower"
              info={selected.detail.primary_borrower}
            />
          ) : (
            <p>No primary borrower projection is available.</p>
          )}

          {selected.detail.co_borrower ? (
            <BorrowerInfo
              label="Co-borrower"
              info={selected.detail.co_borrower}
            />
          ) : null}

          <section aria-labelledby="agent-request-heading">
            <h3 id="agent-request-heading">Mortgage request</h3>
            <pre>{formatJson(selected.detail.mortgage_request ?? null)}</pre>
          </section>

          <section aria-labelledby="agent-subject-heading">
            <h3 id="agent-subject-heading">Subject property</h3>
            <pre>{formatJson(selected.detail.subject_property ?? null)}</pre>
          </section>

          <section aria-labelledby="agent-other-heading">
            <h3 id="agent-other-heading">Other properties</h3>
            <pre>{formatJson(selected.detail.other_properties ?? [])}</pre>
          </section>

          <section aria-labelledby="agent-assets-heading">
            <h3 id="agent-assets-heading">Assets</h3>
            <pre>{formatJson(selected.detail.assets ?? [])}</pre>
          </section>

          <section aria-labelledby="agent-liabilities-heading">
            <h3 id="agent-liabilities-heading">Liabilities</h3>
            <pre>{formatJson(selected.detail.liabilities ?? [])}</pre>
          </section>

          <section aria-labelledby="agent-notes-heading">
            <h3 id="agent-notes-heading">Additional notes</h3>
            <pre>{formatJson(selected.detail.additional_notes ?? null)}</pre>
          </section>

          <section aria-labelledby="agent-documents-heading">
            <h3 id="agent-documents-heading">
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
        </Card>
      ) : null}
    </div>
  );
}
