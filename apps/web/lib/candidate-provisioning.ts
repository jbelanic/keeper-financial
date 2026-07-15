import { apiBaseUrl } from "./recruitment-api";

const SAFE_POSTING = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

export function isSafePostingSlug(value: string): boolean {
  return value.length <= 100 && SAFE_POSTING.test(value);
}

export async function startCandidateApplication(
  token: string,
  posting: string,
  fetcher: typeof fetch = fetch,
): Promise<{ id: string }> {
  if (!isSafePostingSlug(posting)) throw new Error("invalid posting");
  const response = await fetcher(
    `${apiBaseUrl()}/api/v1/recruitment/postings/${posting}/applications/start`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    },
  );
  if (!response.ok) throw new Error("application provisioning failed");
  const data = (await response.json()) as { id?: unknown };
  if (typeof data.id !== "string")
    throw new Error("invalid application response");
  return { id: data.id };
}
