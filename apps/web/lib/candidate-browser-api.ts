import { createKeeperBrowserClient } from "./supabase-browser";
import { apiBaseUrl } from "./recruitment-api";

export type CandidateValidationIssue = {
  path: Array<string | number>;
  message: string;
};

export class CandidateRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly issues: CandidateValidationIssue[] = [],
    public readonly detail: string | null = null,
  ) {
    super(`candidate request failed (${status})`);
  }
}

function boundedText(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const clean = value.replace(/[\u0000-\u001f\u007f]/g, " ").trim();
  return clean ? clean.slice(0, 240) : null;
}

async function candidateRequestError(
  response: Response,
): Promise<CandidateRequestError> {
  if (response.status !== 409 && response.status !== 422) {
    return new CandidateRequestError(response.status);
  }
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (Array.isArray(payload.detail)) {
      const issues = payload.detail.flatMap(
        (item): CandidateValidationIssue[] => {
          if (!item || typeof item !== "object") return [];
          const record = item as { loc?: unknown; msg?: unknown };
          if (!Array.isArray(record.loc)) return [];
          const path = record.loc.filter(
            (part): part is string | number =>
              (typeof part === "string" && /^[a-z_]+$/.test(part)) ||
              (typeof part === "number" &&
                Number.isInteger(part) &&
                part >= 0 &&
                part <= 20),
          );
          const message = boundedText(record.msg);
          return message ? [{ path, message }] : [];
        },
      );
      return new CandidateRequestError(response.status, issues);
    }
    return new CandidateRequestError(
      response.status,
      [],
      boundedText(payload.detail),
    );
  } catch {
    return new CandidateRequestError(response.status);
  }
}

export async function candidateBrowserRequest(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const supabase = createKeeperBrowserClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("candidate session unavailable");
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(`${apiBaseUrl()}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function candidateBrowserJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await candidateBrowserRequest(path, init);
  if (!response.ok) throw await candidateRequestError(response);
  return (await response.json()) as T;
}
