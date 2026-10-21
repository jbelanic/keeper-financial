import type { PortalArea } from "@keeper/contracts";

// The API answers every portal-access probe with the caller's own role list, so
// one call yields both "may I open this area" and "which other portals does this
// account hold". The API stays authoritative: this only decides navigation,
// never authorization.
export type PortalAccess = { roles: string[] };

export async function portalAccessRequest(
  token: string,
  area: PortalArea,
  fetcher: typeof fetch = fetch,
): Promise<PortalAccess | null> {
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  let response: Response;
  try {
    response = await fetcher(`${baseUrl}/api/v1/auth/access?area=${area}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    return null;
  }
  if (!response.ok) return null;
  try {
    const body = (await response.json()) as { roles?: unknown };
    const roles = Array.isArray(body.roles)
      ? body.roles.filter((role): role is string => typeof role === "string")
      : [];
    return { roles };
  } catch {
    return { roles: [] };
  }
}
