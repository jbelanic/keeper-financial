import { apiBaseUrl } from "./recruitment-api";
import { getSupabaseServerClient } from "./supabase-server";

export async function portalServerJson<T>(path: string): Promise<T | null> {
  try {
    const supabase = await getSupabaseServerClient();
    const { data: userData, error } = await supabase.auth.getUser();
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (error || !userData.user || !token) return null;
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
    if (!response.ok) return null;
    return (await response.json()) as T;
  } catch {
    return null;
  }
}
