import type { components } from "@keeper/contracts";
import { apiBaseUrl } from "./recruitment-api";
import { getSupabaseServerClient } from "./supabase-server";

export type PublicAgentProfile = components["schemas"]["PublicAgentProfile"];
export type PublicAgentProfileList =
  components["schemas"]["PublicAgentProfileList"];
export type AdminAgentProfile = components["schemas"]["AdminAgentProfile"];
export type AdminAgentProfileList =
  components["schemas"]["AdminAgentProfileList"];

async function optionalServerBearer(): Promise<Headers> {
  const headers = new Headers();
  try {
    const supabase = await getSupabaseServerClient();
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (token) headers.set("Authorization", `Bearer ${token}`);
  } catch {
    // Public operations remain anonymous when there is no server session.
  }
  return headers;
}

async function publicAgentResponse(path: string): Promise<Response> {
  return fetch(`${apiBaseUrl()}${path}`, {
    headers: await optionalServerBearer(),
    cache: "no-store",
  });
}

export async function getPublishedAgents(): Promise<PublicAgentProfileList> {
  const response = await publicAgentResponse(
    "/api/v1/agents?limit=25&offset=0",
  );
  if (!response.ok) throw new Error("published agent directory unavailable");
  return (await response.json()) as PublicAgentProfileList;
}

export async function getPublishedAgent(
  slug: string,
): Promise<PublicAgentProfile | null> {
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug) || slug.length > 100)
    return null;
  const response = await publicAgentResponse(
    `/api/v1/agents/${encodeURIComponent(slug)}`,
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("published agent profile unavailable");
  return (await response.json()) as PublicAgentProfile;
}
