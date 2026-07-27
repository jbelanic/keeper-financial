import type { PortalArea } from "@keeper/contracts";

export async function portalAccessRequest(
  token: string,
  area: PortalArea,
  fetcher: typeof fetch = fetch,
): Promise<boolean> {
  const baseUrl = process.env.API_INTERNAL_URL ?? "http://localhost:8000";
  const response = await fetcher(`${baseUrl}/api/v1/auth/access?area=${area}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
    signal: AbortSignal.timeout(10_000),
  });
  return response.ok;
}
