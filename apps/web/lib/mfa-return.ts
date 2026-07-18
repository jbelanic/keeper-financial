export type MfaReturnTo =
  | "/admin"
  | "/candidate"
  | `/candidate/applications/${string}#documents`;

const CANDIDATE_DOCUMENT_RETURN =
  /^\/candidate\/applications\/[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}#documents$/i;

export function safeMfaReturnTo(
  value: string | string[] | undefined,
): MfaReturnTo {
  if (value === "/admin" || value === "/candidate") return value;
  if (typeof value === "string" && CANDIDATE_DOCUMENT_RETURN.test(value)) {
    return value as MfaReturnTo;
  }
  return "/candidate";
}

export function candidateDocumentMfaReturn(applicationId: string): string {
  return `/auth/mfa?returnTo=${encodeURIComponent(`/candidate/applications/${applicationId}#documents`)}`;
}
