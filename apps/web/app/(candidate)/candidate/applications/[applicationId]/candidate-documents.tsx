"use client";

import { createKeeperBrowserClient } from "@/lib/supabase-browser";
import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Button, ErrorState, FormField, StatusBadge } from "@keeper/ui";
import { candidateBrowserRequest } from "@/lib/candidate-browser-api";
import { candidateDocumentMfaReturn } from "@/lib/mfa-return";
import type {
  CandidateApplication,
  CandidateDocument,
  CandidateDocumentList,
} from "@/lib/recruitment-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;
type CandidateMfaState = "loading" | "enroll" | "verify" | "aal2" | "error";
type DocumentLoadState = "idle" | "loading" | "loaded" | "error";

const safeUploadErrors: Record<string, string> = {
  unsupported_category:
    "Select either Résumé/CV or Cover letter before uploading.",
  unsupported_extension:
    "This file type is not supported. Choose a PDF, DOC, or DOCX file.",
  invalid_filename:
    "This file name cannot be accepted. Rename the file and try again.",
  declared_mime_mismatch:
    "The file type reported by your browser does not match its extension.",
  detected_mime_mismatch:
    "The file contents do not match the selected PDF, DOC, or DOCX type.",
  pdf_structure_invalid:
    "This PDF could not be read safely. Export a new PDF and try again.",
  docx_structure_invalid:
    "This DOCX could not be read safely. Save a new DOCX and try again.",
  legacy_doc_invalid:
    "This DOC could not be read safely. Save a new DOC or DOCX and try again.",
  file_too_large: "This file is larger than 10 MiB. Choose a smaller document.",
  empty_file: "This file is empty. Choose a document with content.",
  malware_detected:
    "This document failed its security scan and was not stored.",
  scanner_unavailable:
    "Security scanning is temporarily unavailable. The document was not stored; try again later.",
  storage_unavailable:
    "Private document storage is temporarily unavailable. The document was not saved; try again later.",
};

async function safeUploadError(response: Response): Promise<string> {
  if (response.status === 401 || response.status === 403) {
    return "MFA step-up is required before private document metadata or files can be accessed.";
  }
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string" && safeUploadErrors[body.detail]) {
      return safeUploadErrors[body.detail];
    }
  } catch {
    // The bounded fallback below intentionally does not expose provider data.
  }
  if ([413, 415, 422].includes(response.status)) {
    return "This file is unsupported or invalid. Choose a valid PDF, DOC, or DOCX file no larger than 10 MiB.";
  }
  if (response.status === 503) {
    return "The private document service is temporarily unavailable. The document was not stored; try again later.";
  }
  return "The document could not be uploaded and was not released for download.";
}

function deniedMessage(status: number): string {
  return status === 403
    ? "MFA step-up is required before private document metadata or files can be accessed."
    : "Private documents are unavailable. No public file link has been created.";
}

async function inspectCandidateMfa(): Promise<CandidateMfaState> {
  const supabase = createKeeperBrowserClient();
  const assurance = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
  if (assurance.error || !assurance.data)
    throw new Error("assurance unavailable");
  if (assurance.data.currentLevel === "aal2") return "aal2";
  const factors = await supabase.auth.mfa.listFactors();
  if (factors.error || !factors.data) throw new Error("factors unavailable");
  return factors.data.totp.some((factor) => factor.status === "verified")
    ? "verify"
    : "enroll";
}

export function CandidateDocuments({
  applicationId,
  applicationState,
  applicationStatus,
  requester = candidateBrowserRequest,
  inspectMfa = inspectCandidateMfa,
}: {
  applicationId: string;
  applicationState: "draft" | "submitted" | "withdrawn";
  applicationStatus: CandidateApplication["status"];
  requester?: Requester;
  inspectMfa?: () => Promise<CandidateMfaState>;
}) {
  const [documents, setDocuments] = useState<CandidateDocument[]>([]);
  const [selected, setSelected] = useState<File | null>(null);
  const [announcement, setAnnouncement] = useState("");
  const [error, setError] = useState("");
  const [actionBusy, setActionBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documentState, setDocumentState] = useState<DocumentLoadState>("idle");
  const [mfaState, setMfaState] = useState<CandidateMfaState>("loading");
  const categoryRef = useRef<HTMLSelectElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const loadInFlightRef = useRef(false);
  const active =
    applicationState !== "withdrawn" &&
    !["withdrawn", "declined"].includes(applicationStatus);
  const mfaReturn = candidateDocumentMfaReturn(applicationId);

  const loadDocuments = useCallback(async () => {
    if (loadInFlightRef.current) return;
    loadInFlightRef.current = true;
    setDocumentState("loading");
    setError("");
    setAnnouncement("Loading private documents…");
    try {
      const response = await requester(
        `/api/v1/candidate/applications/${applicationId}/documents`,
      );
      if (!response.ok) {
        if (response.status === 403) setMfaState("verify");
        setError(deniedMessage(response.status));
        setAnnouncement("");
        setDocumentState("error");
        return;
      }
      const result = (await response.json()) as CandidateDocumentList;
      setDocuments(result.items);
      setDocumentState("loaded");
      setAnnouncement(
        `${result.items.length} private document${result.items.length === 1 ? "" : "s"} loaded.`,
      );
    } catch {
      setError(
        "Private documents are unavailable. No public file link has been created.",
      );
      setAnnouncement("");
      setDocumentState("error");
    } finally {
      loadInFlightRef.current = false;
    }
  }, [applicationId, requester]);

  useEffect(() => {
    let activeInspection = true;
    async function inspect() {
      try {
        const result = await inspectMfa();
        if (!activeInspection) return;
        setMfaState(result);
        if (result === "aal2") await loadDocuments();
      } catch {
        if (activeInspection) setMfaState("error");
      }
    }
    void inspect();
    return () => {
      activeInspection = false;
    };
  }, [inspectMfa, loadDocuments]);

  async function retryMfaInspection() {
    setMfaState("loading");
    try {
      const result = await inspectMfa();
      setMfaState(result);
      if (result === "aal2") await loadDocuments();
    } catch {
      setMfaState("error");
    }
  }

  async function upload() {
    if (!selected || !categoryRef.current || uploading || actionBusy) return;
    setUploading(true);
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
        if (response.status === 403) setMfaState("verify");
        setError(await safeUploadError(response));
        setAnnouncement("");
        return;
      }
      const document = (await response.json()) as CandidateDocument;
      setSelected(null);
      if (fileInputRef.current) fileInputRef.current.value = "";

      const refreshed = await requester(
        `/api/v1/candidate/applications/${applicationId}/documents`,
      );
      if (!refreshed.ok) {
        setDocumentState("error");
        setError(
          "The document was uploaded, but the private document list could not be refreshed. Try loading the list again.",
        );
        setAnnouncement("Document upload completed.");
        return;
      }
      const result = (await refreshed.json()) as CandidateDocumentList;
      setDocuments(result.items);
      setDocumentState("loaded");
      setAnnouncement(
        document.quarantined
          ? "Document uploaded and quarantined while security scanning is pending."
          : "Document uploaded, scanned, and listed successfully.",
      );
    } catch {
      setError(
        "The document could not be uploaded. Try again after confirming MFA and connectivity.",
      );
      setAnnouncement("");
    } finally {
      setUploading(false);
    }
  }

  async function download(document: CandidateDocument) {
    if (actionBusy || uploading) return;
    setActionBusy(true);
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
      setActionBusy(false);
    }
  }

  async function remove(document: CandidateDocument) {
    if (actionBusy || uploading) return;
    setActionBusy(true);
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
      setActionBusy(false);
    }
  }

  return (
    <section
      id="documents"
      className="card document-workflow"
      aria-labelledby="documents-heading"
      tabIndex={-1}
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
      {mfaState === "loading" ? (
        <p role="status">Checking document security…</p>
      ) : mfaState === "enroll" ? (
        <p>
          <Link className="button button-primary" href={mfaReturn}>
            Set up MFA to access documents
          </Link>
        </p>
      ) : mfaState === "verify" ? (
        <p>
          <Link className="button button-primary" href={mfaReturn}>
            Verify with MFA to access documents
          </Link>
        </p>
      ) : mfaState === "error" ? (
        <div>
          <ErrorState title="Document security check unavailable">
            Multi-factor authentication status could not be verified. No private
            document request was made.
          </ErrorState>
          <Button type="button" onClick={retryMfaInspection}>
            Try security check again
          </Button>
        </div>
      ) : null}
      {mfaState === "aal2" && documentState === "loading" ? (
        <p role="status">Loading your uploaded documents…</p>
      ) : null}
      {mfaState === "aal2" && documentState === "error" ? (
        <Button type="button" onClick={loadDocuments}>
          Try loading uploaded documents again
        </Button>
      ) : null}
      {mfaState === "aal2" && documentState === "loaded" && active ? (
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
              ref={fileInputRef}
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
          <Button
            type="button"
            onClick={upload}
            disabled={!selected || uploading || actionBusy}
          >
            {uploading ? "Uploading…" : "Upload document"}
          </Button>
        </div>
      ) : mfaState === "aal2" && documentState === "loaded" ? (
        <p className="notice">
          New document uploads ended when this application became terminal.
        </p>
      ) : null}
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
                  disabled={actionBusy || uploading || document.quarantined}
                >
                  Download privately
                </Button>
                {applicationState === "draft" ? (
                  <Button
                    type="button"
                    className="button-danger"
                    onClick={() => remove(document)}
                    disabled={actionBusy || uploading}
                  >
                    Remove draft document
                  </Button>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      ) : documentState === "loaded" ? (
        <p>No documents uploaded yet.</p>
      ) : null}
    </section>
  );
}
