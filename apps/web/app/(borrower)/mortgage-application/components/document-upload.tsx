"use client";

import { useEffect, useState } from "react";
import {
  listBorrowerDocuments,
  removeBorrowerDocument,
  uploadBorrowerDocument,
  type BorrowerDocument,
} from "@/lib/borrower-application-api";

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
              : "No documents uploaded.",
          );
          onSettledChange(true);
        }
      })
      .catch(
        () => active && setStatus("Documents could not be loaded. Try again."),
      );
    return () => {
      active = false;
    };
  }, [applicationId, onSettledChange]);

  async function upload() {
    if (!file || (category === "other" && !description.trim())) {
      setStatus("Choose a file and describe documents categorized as Other.");
      return;
    }
    setBusy(true);
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
      setStatus("Document uploaded securely.");
      onSettledChange(true);
    } catch {
      try {
        const documents = await listBorrowerDocuments(applicationId);
        setItems(documents);
        setStatus(
          "The upload response was uncertain. The authoritative document list was reloaded.",
        );
        onSettledChange(true);
      } catch {
        setStatus(
          "The upload result could not be reconciled. Reload the current document list before continuing.",
        );
        onSettledChange(false);
      }
    } finally {
      setBusy(false);
    }
  }

  async function remove(documentId: string) {
    setBusy(true);
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
          setStatus(
            "Document removal did not complete. Retry removal before continuing.",
          );
          onSettledChange(false);
        } else {
          setStatus("Document removal was confirmed by the current list.");
          onSettledChange(true);
        }
      } catch {
        setStatus(
          "The removal result could not be reconciled. Reload the current document list before continuing.",
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
      <label>
        Category
        <select
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          {categories.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      {category === "other" ? (
        <label>
          Other document description (required)
          <input
            maxLength={200}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </label>
      ) : null}
      <label>
        Select a PDF, DOC, DOCX, JPEG, or PNG
        <input
          type="file"
          accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </label>
      <button
        type="button"
        disabled={busy || !file}
        onClick={() => void upload()}
      >
        {busy ? "Document operation in progress…" : "Upload document"}
      </button>
      <p aria-live="polite">{status}</p>
      <ul>
        {items.map((item) => (
          <li key={item.document_id}>
            <span>
              {item.filename} — {item.category} — {item.size_bytes} bytes
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
