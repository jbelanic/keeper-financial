import type { components } from "@keeper/contracts";

export type PublicPosting = components["schemas"]["PublicPosting"];
export type PublicPostingList = components["schemas"]["PublicPostingList"];
export type CandidateApplication =
  components["schemas"]["CandidateApplicationResponse"];
export type CandidateApplicationList =
  components["schemas"]["ApplicationListResponse"];
export type CandidatePrivacyDisclosure =
  components["schemas"]["CandidatePrivacyDisclosureResponse"];
export type CandidateDocument =
  components["schemas"]["CandidateDocumentResponse"];
export type CandidateDocumentList =
  components["schemas"]["CandidateDocumentList"];
export type AdminPosting = components["schemas"]["AdminPosting"];
export type AdminPostingList = components["schemas"]["AdminPostingList"];

export const apiBaseUrl = () =>
  process.env.API_INTERNAL_URL ?? "http://localhost:8000";

export async function getPublishedPostings(): Promise<PublicPostingList> {
  const response = await fetch(
    `${apiBaseUrl()}/api/v1/recruitment/postings?limit=25&offset=0`,
    { next: { revalidate: 60 } },
  );
  if (!response.ok) throw new Error("published postings unavailable");
  return (await response.json()) as PublicPostingList;
}

export async function getPublishedPosting(
  slug: string,
): Promise<PublicPosting | null> {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100)
    return null;
  const response = await fetch(
    `${apiBaseUrl()}/api/v1/recruitment/postings/${encodeURIComponent(slug)}`,
    { next: { revalidate: 60 } },
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("published posting unavailable");
  return (await response.json()) as PublicPosting;
}
