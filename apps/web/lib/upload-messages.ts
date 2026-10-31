/**
 * One sentence for every way a supporting document can be refused.
 *
 * The API describes a rejection with a stable code (`pdf_structure_invalid`,
 * `file_too_large`, `malware_detected`, …). The upload panel used to collapse
 * all of them into "The upload response was uncertain", which told the applicant
 * neither what was wrong nor what to do — and, because the notice replaced the
 * list, it also hid what had already been uploaded.
 */

import { BorrowerApplicationError } from "@/lib/borrower-application-api";

const REASONS: Record<string, string> = {
  invalid_category: "Choose a document category before uploading.",
  description_required:
    "Describe the document when the category is Other, then upload it again.",
  description_not_allowed:
    "Only documents categorized as Other take a description. Clear it, or change the category.",
  description_too_long: "Keep the description to 200 characters or fewer.",
  invalid_filename:
    "That file name is not usable. Rename the file and try again.",
  unsupported_extension:
    "That file type is not accepted. Upload a PDF, DOC, DOCX, JPEG, or PNG.",
  detected_mime_mismatch:
    "The file's contents do not match its type. Save it again in a supported format and re-upload.",
  pdf_structure_invalid:
    "That PDF could not be read — it may be damaged or only partly saved. Re-save or re-scan it, then upload again.",
  malformed: "That file could not be read. Re-save it, then upload again.",
  legacy_doc_invalid:
    "That older .doc file could not be read. Save it as PDF or DOCX and upload that.",
  file_too_large: "That file is larger than the 25 MB limit for one document.",
  aggregate_size_limit:
    "Your documents already reach the 250 MB total limit. Remove one before uploading another.",
  document_count_limit:
    "You have reached the maximum number of documents. Remove one before uploading another.",
  malware_detected:
    "We blocked that file because the virus scan flagged it. Try a fresh copy from a trusted source, or contact us.",
  document_uploads_unavailable:
    "Documents can no longer be changed on this application. Nothing was uploaded.",
  application_not_found:
    "This browser can no longer access the draft. Nothing was uploaded.",
  invalid_upload_fields:
    "The upload did not arrive in a usable form. Try again.",
  unexpected_upload_field:
    "The upload did not arrive in a usable form. Try again.",
  malformed_multipart: "The upload did not arrive in a usable form. Try again.",
};

/** A clear sentence for a refused upload, including unusable-service cases. */
export function uploadFailureMessage(error: unknown): string {
  if (error instanceof BorrowerApplicationError) {
    if (error.status === 503) {
      return "Document scanning or storage is unavailable right now, so nothing was uploaded. Try again shortly.";
    }
    if (error.status === 429) {
      return "Too many uploads in a short time. Wait a moment and try again.";
    }
    if (error.code && REASONS[error.code]) return REASONS[error.code];
    if (error.status === 413) {
      return "That file is too large for the current limits.";
    }
    if (error.status === 422) {
      return "That document was not accepted. Check the category and the file, then try again.";
    }
  }
  return "The document could not be uploaded. Check your connection and try again; nothing was added.";
}
