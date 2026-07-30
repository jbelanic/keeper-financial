import type { components } from "@keeper/contracts";
import { getSupabaseServerClient } from "./supabase-server";

export const LEADS_PAGE_SIZE = 25;
export const LEAD_STATUSES = [
  "new",
  "assigned",
  "contacted",
  "closed",
] as const;
export type LeadStatus = (typeof LEAD_STATUSES)[number];

export type ConsentState = components["schemas"]["ConsentState"];
export type AdminLead = components["schemas"]["LeadListItem"];
export type AdminLeadList = components["schemas"]["LeadListResponse"];
export type LeadStatusUpdated = components["schemas"]["LeadStatusUpdated"];

type QueueParams = { page: number; status?: LeadStatus };

export function parseLeadQueueSearchParams(
  input: Record<string, string | string[] | undefined>,
): QueueParams {
  const rawPage = typeof input.page === "string" ? input.page : "";
  const parsedPage = /^\d+$/.test(rawPage) ? Number(rawPage) : 1;
  const page = parsedPage >= 1 && parsedPage <= 10_000 ? parsedPage : 1;
  const status =
    typeof input.status === "string" &&
    LEAD_STATUSES.includes(input.status as LeadStatus)
      ? (input.status as LeadStatus)
      : undefined;
  return { page, status };
}

export async function adminLeadListRequest(
  token: string,
  params: QueueParams,
  fetcher: typeof fetch = fetch,
): Promise<AdminLeadList> {
  const query = new URLSearchParams({
    limit: String(LEADS_PAGE_SIZE),
    offset: String((params.page - 1) * LEADS_PAGE_SIZE),
  });
  if (params.status) query.set("status", params.status);
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const response = await fetcher(
    `${baseUrl}/api/v1/leads?${query.toString()}`,
    {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    },
  );
  if (!response.ok) throw new Error("lead queue unavailable");
  return (await response.json()) as AdminLeadList;
}

export async function adminMarketingWithdrawalRequest(
  token: string,
  leadId: string,
  fetcher: typeof fetch = fetch,
): Promise<ConsentState> {
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      leadId,
    )
  ) {
    throw new Error("invalid lead identifier");
  }
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const response = await fetcher(
    `${baseUrl}/api/v1/leads/${leadId}/marketing-consent/withdrawal`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    },
  );
  if (!response.ok) throw new Error("marketing consent withdrawal unavailable");
  return (await response.json()) as ConsentState;
}

export async function adminLeadStatusRequest(
  token: string,
  leadId: string,
  status: LeadStatus,
  fetcher: typeof fetch = fetch,
): Promise<LeadStatusUpdated> {
  if (
    !/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
      leadId,
    )
  ) {
    throw new Error("invalid lead identifier");
  }
  if (!LEAD_STATUSES.includes(status)) throw new Error("invalid lead status");
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const response = await fetcher(`${baseUrl}/api/v1/leads/${leadId}/status`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error("lead status update unavailable");
  return (await response.json()) as LeadStatusUpdated;
}

async function adminToken(): Promise<string> {
  const supabase = await getSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) throw new Error("administrator session unavailable");
  return token;
}

export async function fetchAdminLeadList(
  params: QueueParams,
): Promise<AdminLeadList> {
  return adminLeadListRequest(await adminToken(), params);
}

export async function withdrawAdminLeadMarketing(
  leadId: string,
): Promise<ConsentState> {
  return adminMarketingWithdrawalRequest(await adminToken(), leadId);
}

export async function updateAdminLeadStatus(
  leadId: string,
  status: LeadStatus,
): Promise<LeadStatusUpdated> {
  return adminLeadStatusRequest(await adminToken(), leadId, status);
}
