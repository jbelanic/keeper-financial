import type { components } from "@keeper/contracts";

export type BorrowerDraftStart =
  components["schemas"]["BorrowerApplicationStartResponse"];
export type BorrowerDraft =
  components["schemas"]["BorrowerApplicationSaveResponse"];
export type BorrowerDraftPayload = Record<string, unknown>;

const API_ROOT = "/api/v1/borrower-applications";
const APPLICATION_ID_KEY = "keeper.borrower.application-id";

export type BorrowerValidationIssue = {
  path: Array<string | number>;
  message: string;
};

export class BorrowerApplicationError extends Error {
  constructor(
    public readonly status: number,
    public readonly issues: BorrowerValidationIssue[] = [],
  ) {
    super(`borrower application request failed (${status})`);
  }
}

function safeIssuePath(value: unknown): Array<string | number> {
  if (!Array.isArray(value)) return [];
  return value.filter(
    (part): part is string | number =>
      (typeof part === "string" && /^[a-z_]+$/.test(part)) ||
      (typeof part === "number" &&
        Number.isInteger(part) &&
        part >= 0 &&
        part <= 50),
  );
}

async function responseError(
  response: Response,
): Promise<BorrowerApplicationError> {
  if (response.status !== 409 && response.status !== 422) {
    return new BorrowerApplicationError(response.status);
  }
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (!Array.isArray(payload.detail)) {
      return new BorrowerApplicationError(response.status);
    }
    const issues = payload.detail.flatMap((item): BorrowerValidationIssue[] => {
      if (!item || typeof item !== "object") return [];
      const issue = item as { loc?: unknown; msg?: unknown };
      const message =
        typeof issue.msg === "string"
          ? issue.msg.replace(/[\u0000-\u001f\u007f]/g, " ").slice(0, 200)
          : "";
      return message ? [{ path: safeIssuePath(issue.loc), message }] : [];
    });
    return new BorrowerApplicationError(response.status, issues);
  } catch {
    return new BorrowerApplicationError(response.status);
  }
}

async function borrowerJson<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (init.method && init.method !== "GET") {
    headers.set("X-Keeper-Borrower-CSRF", "1");
  }
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    headers,
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) throw await responseError(response);
  return (await response.json()) as T;
}

export async function startBorrowerDraft(): Promise<BorrowerDraftStart> {
  return borrowerJson<BorrowerDraftStart>("/start", { method: "POST" });
}

export async function getBorrowerDraft(
  applicationId: string,
): Promise<BorrowerDraft> {
  return borrowerJson<BorrowerDraft>(`/${encodeURIComponent(applicationId)}`, {
    method: "GET",
  });
}

export async function patchBorrowerDraft(
  applicationId: string,
  expectedRevision: number,
  payload: BorrowerDraftPayload,
): Promise<BorrowerDraft> {
  return borrowerJson<BorrowerDraft>(`/${encodeURIComponent(applicationId)}`, {
    method: "PATCH",
    body: JSON.stringify({
      expected_revision: expectedRevision,
      payload,
    }),
  });
}

export function readBorrowerApplicationId(): string | null {
  if (typeof window === "undefined") return null;
  const value = window.sessionStorage.getItem(APPLICATION_ID_KEY);
  return value && /^[0-9a-f-]{36}$/i.test(value) ? value : null;
}

export function rememberBorrowerApplicationId(applicationId: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(APPLICATION_ID_KEY, applicationId);
}

export function forgetBorrowerApplicationId(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(APPLICATION_ID_KEY);
}

export async function recoverOrStartBorrowerDraft(): Promise<{
  draft: BorrowerDraft | BorrowerDraftStart;
  recovered: boolean;
}> {
  const applicationId = readBorrowerApplicationId();
  if (applicationId) {
    try {
      return {
        draft: await getBorrowerDraft(applicationId),
        recovered: true,
      };
    } catch (error) {
      if (
        !(error instanceof BorrowerApplicationError) ||
        ![403, 404].includes(error.status)
      ) {
        throw error;
      }
      forgetBorrowerApplicationId();
    }
  }
  const draft = await startBorrowerDraft();
  rememberBorrowerApplicationId(draft.application_id);
  return { draft, recovered: false };
}
