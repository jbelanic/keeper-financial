"use client";

import { useRef, useState } from "react";
import { Button, ErrorState, FormField, StatusBadge } from "@keeper/ui";
import { candidateBrowserRequest } from "@/lib/candidate-browser-api";
import type {
  CandidateDocument,
  CandidateDocumentList,
} from "@/lib/recruitment-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

export function CandidateDocuments({
  applicationId,
  applicationState,
  applicationStatus,
  requester = candidateBrowserRequest,
}: {
  applicationId: string;
  applicationState: "draft" | "submitted" | "withdrawn";
  applicationStatus:
    | "application_started"
    | "application_submitted"
    | "withdrawn"
    | "declined";
  requester?: Requester;
}) {
  const [documents, setDocuments] = useState<CandidateDocument[]>([]);
  const [selected, setSelected] = useState<File | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const categoryRef = useRef<HTMLSelectElement>(null);
  const active =
    applicationState !== "withdrawn" &&
    !["withdrawn", "declined"].includes(applicationStatus);

  function deniedMessage(status: number) {
    return status === 403
      ? "MFA step-up is required before private document metadata or files can be accessed."
      : "Private documents are unavailable. No public file link has been created.";
  }

  async function loadDocuments() {
    if (busy) return;
    setBusy(true);
    setError("");
    setAnnouncement("Loading private documents…");
    try {
      const response = await requester(
        `/api/v1/candidate/applications/${applicationId}/documents`,
      );
      if (!response.ok) {
        setError(deniedMessage(response.status));
        setAnnouncement("");
        return;
      }
      const result = (await response.json()) as CandidateDocumentList;
      setDocuments(result.items);
      setLoaded(true);
      setAnnouncement(
        `${result.items.length} private document${result.items.length === 1 ? "" : "s"} loaded.`,
      );
    } catch {
      setError(
        "Private documents are unavailable. No public file link has been created.",
      );
      setAnnouncement("");
    } finally {
      setBusy(false);
    }
  }

  async function upload() {
    if (!selected || !categoryRef.current || busy) return;
    setBusy(true);
    setError("");
    setAnnouncement(
      `Uploading ${selected.name} for validation and security scanning…`,
    );
    const form = new FormData();
    form.set("category", categoryRef.current.value);
    form.set("file", selected);
    try {
      const response = await requester(
        `/api/v1/candidate/applications/${applicationId}/documents`,
        { method: "POST", body: form },
      );
      if (!response.ok) {
        setError(
          response.status === 403
            ? deniedMessage(403)
            : "The document was rejected or scanning is unavailable. It has not been released for download.",
        );
        setAnnouncement("");
        return;
      }
      const document = (await response.json()) as CandidateDocument;
      setDocuments((items) => [...items, document]);
      setLoaded(true);
      setSelected(null);
      setAnnouncement(
        document.quarantined
          ? "Document uploaded and quarantined while security scanning is pending."
          : "Document uploaded and available after the security decision.",
      );
    } catch {
      setError(
        "The document could not be uploaded. Try again after confirming MFA and connectivity.",
      );
      setAnnouncement("");
    } finally {
      setBusy(false);
    }
  }

  async function download(document: CandidateDocument) {
    if (busy) return;
    setBusy(true);
    setError("");
    setAnnouncement("Authorizing private document download…");
    try {
      const response = await requester(
        `/api/v1/documents/${document.id}/download`,
      );
      if (!response.ok) {
        setError(
          response.status === 403
            ? deniedMessage(403)
            : "This document is quarantined, unavailable, or no longer eligible for download.",
        );
        setAnnouncement("");
        return;
      }
      const objectUrl = URL.createObjectURL(await response.blob());
      const link = window.document.createElement("a");
      link.href = objectUrl;
      link.download = document.original_filename;
      link.click();
      URL.revokeObjectURL(objectUrl);
      setAnnouncement("Private document download authorized.");
    } catch {
      setError("The private document could not be downloaded.");
      setAnnouncement("");
    } finally {
      setBusy(false);
    }
  }

  async function remove(document: CandidateDocument) {
    if (busy) return;
    setBusy(true);
    try {
      const response = await requester(
        `/api/v1/candidate/applications/${applicationId}/documents/${document.id}`,
        { method: "DELETE" },
      );
      if (!response.ok) {
        setError("The draft document could not be removed.");
        return;
      }
      setDocuments((items) => items.filter((item) => item.id !== document.id));
      setAnnouncement("Draft document removed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      className="card document-workflow"
      aria-labelledby="documents-heading"
    >
      <h2 id="documents-heading">Supporting documents (optional)</h2>
      <p>
        Résumés and cover letters are optional. PDF, DOC, and DOCX files are
        limited to 10 MiB and remain private. Document actions require MFA.
      </p>
      <p role="status" aria-live="polite">
        {announcement}
      </p>
      {error ? (
        <ErrorState title="Private document action unavailable">
          {error}
        </ErrorState>
      ) : null}
      {!loaded ? (
        <Button type="button" onClick={loadDocuments} disabled={busy}>
          Load private documents
        </Button>
      ) : null}
      {active ? (
        <div className="document-upload">
          <FormField
            id="candidate-document-category"
            label="Document category (required)"
          >
            <select
              id="candidate-document-category"
              ref={categoryRef}
              defaultValue="resume"
            >
              <option value="resume">Résumé/CV</option>
              <option value="cover_letter">Cover letter</option>
            </select>
          </FormField>
          <FormField
            id="candidate-document-file"
            label="Choose candidate document (required)"
            hint="PDF, DOC, or DOCX; maximum 10 MiB."
          >
            <input
              id="candidate-document-file"
              type="file"
              accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setSelected(file);
                setAnnouncement(
                  file ? `Selected ${file.name}.` : "No document selected.",
                );
              }}
            />
          </FormField>
          <Button type="button" onClick={upload} disabled={!selected || busy}>
            Upload document
          </Button>
        </div>
      ) : (
        <p className="notice">
          New document uploads ended when this application became terminal.
        </p>
      )}
      {documents.length ? (
        <ul className="document-list">
          {documents.map((document) => (
            <li key={document.id}>
              <strong>{document.original_filename}</strong> —{" "}
              {document.category.replace("_", " ")}; security scan:{" "}
              <StatusBadge tone={document.quarantined ? "warning" : "success"}>
                {document.scan_status}
              </StatusBadge>
              <div className="button-row">
                <Button
                  type="button"
                  onClick={() => download(document)}
                  disabled={busy || document.quarantined}
                >
                  Download privately
                </Button>
                {applicationState === "draft" ? (
                  <Button
                    type="button"
                    className="button-danger"
                    onClick={() => remove(document)}
                    disabled={busy}
                  >
                    Remove draft document
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : loaded ? (
        <p>No private documents have been uploaded for this application.</p>
      ) : null}
    </section>
  );
}
