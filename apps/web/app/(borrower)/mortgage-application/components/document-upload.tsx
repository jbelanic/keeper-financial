"use client";

import { useEffect, useState } from "react";
import {
  listBorrowerDocuments,
  removeBorrowerDocument,
  uploadBorrowerDocument,
  type BorrowerDocument,
} from "@/lib/borrower-application-api";
import { uploadFailureMessage } from "@/lib/upload-messages";

const categories = [
  ["income_employment", "Income or employment"],
  ["banking_investment", "Banking or investment"],
  ["down_payment", "Down payment"],
  ["property", "Property"],
  ["tax", "Tax"],
  ["identification", "Identification"],
  ["credit_liability", "Credit or liability"],
  ["other", "Other"],
] as const;

const categoryLabel = (value: string) =>
  categories.find(([code]) => code === value)?.[1] ?? value;

export function DocumentUpload({
  applicationId,
  onSettledChange,
}: {
  applicationId: string;
  onSettledChange: (settled: boolean) => void;
}) {
  const [items, setItems] = useState<BorrowerDocument[]>([]);
  const [category, setCategory] = useState("income_employment");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState("Loading current documents…");
  const [failure, setFailure] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    onSettledChange(false);
    listBorrowerDocuments(applicationId)
      .then((documents) => {
        if (active) {
          setItems(documents);
          setStatus(
            documents.length
              ? "Current documents loaded."
              : "No documents uploaded yet. Supporting documents are optional.",
          );
          onSettledChange(true);
        }
      })
      .catch(() => {
        if (!active) return;
        setFailure(
          "Your current documents could not be loaded. Retry before adding another; nothing has been changed.",
        );
        setStatus("");
      });
    return () => {
      active = false;
    };
  }, [applicationId, onSettledChange]);

  async function upload() {
    if (!file) {
      setFailure("Choose a file to upload first.");
      return;
    }
    if (category === "other" && !description.trim()) {
      setFailure(
        "Describe the document before uploading it as Other, for example “Notice of assessment 2025”.",
      );
      return;
    }
    setBusy(true);
    setFailure(null);
    onSettledChange(false);
    setStatus("Uploading, validating, and scanning…");
    try {
      const document = await uploadBorrowerDocument(
        applicationId,
        file,
        category,
        description.trim() || undefined,
      );
      setItems((current) => [...current, document]);
      setFile(null);
      setDescription("");
      setStatus("Document uploaded and scanned successfully.");
      onSettledChange(true);
    } catch (error) {
      // Keep the authoritative list on screen and say why the file was refused.
      setFailure(uploadFailureMessage(error));
      try {
        setItems(await listBorrowerDocuments(applicationId));
        setStatus("Your saved documents are listed below.");
        onSettledChange(true);
      } catch {
        setStatus("");
        onSettledChange(false);
      }
    } finally {
      setBusy(false);
    }
  }

  async function remove(documentId: string) {
    setBusy(true);
    setFailure(null);
    onSettledChange(false);
    try {
      await removeBorrowerDocument(applicationId, documentId);
      setItems((current) =>
        current.filter((item) => item.document_id !== documentId),
      );
      setStatus("Document removed.");
      onSettledChange(true);
    } catch {
      try {
        const documents = await listBorrowerDocuments(applicationId);
        setItems(documents);
        if (documents.some((item) => item.document_id === documentId)) {
          setFailure(
            "That document is still on the application. Retry removal before continuing.",
          );
          onSettledChange(false);
        } else {
          setStatus("Document removal was confirmed by the current list.");
          onSettledChange(true);
        }
      } catch {
        setFailure(
          "The removal result could not be confirmed. Reload this page before continuing; nothing was changed in the browser.",
        );
        onSettledChange(false);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-labelledby="borrower-documents-heading">
      <h3 id="borrower-documents-heading">Supporting documents</h3>
      <p>
        Upload one file at a time — PDF, DOC, DOCX, JPEG, or PNG, up to 25 MB
        each. Every file is virus-scanned before it is stored.
      </p>
      <div className="form-field">
        <label htmlFor="borrower-document-category">Category</label>
        <select
          id="borrower-document-category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          {categories.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>
      {category === "other" ? (
        <div className="form-field">
          <label htmlFor="borrower-document-description">
            Other document description (required)
          </label>
          <input
            id="borrower-document-description"
            maxLength={200}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
      ) : null}
      <div className="form-field">
        <label htmlFor="borrower-document-file">
          Select a PDF, DOC, DOCX, JPEG, or PNG
        </label>
        <input
          id="borrower-document-file"
          type="file"
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </div>
      <button
        type="button"
        disabled={busy || !file}
        onClick={() => void upload()}
      >
        {busy ? "Document operation in progress…" : "Upload document"}
      </button>
      <p aria-live="polite">{status}</p>
      {failure ? (
        <p role="alert" className="field-error">
          {failure}
        </p>
      ) : null}
      <p>
        {items.length
          ? `${items.length} document${items.length === 1 ? "" : "s"} on this application:`
          : "No documents uploaded yet."}
      </p>
      <ul>
        {items.map((item) => (
          <li key={item.document_id}>
            <span>
              {item.filename} — {categoryLabel(item.category)} —{" "}
              {Math.round(item.size_bytes / 1024)} KB —{" "}
              {item.scan_status === "clean" ? "scanned, clean" : item.scan_status}
            </span>{" "}
            <button
              type="button"
              disabled={busy}
              onClick={() => void remove(item.document_id)}
            >
              Remove {item.filename}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
