import { apiBaseUrl } from "./recruitment-api";
import { getSupabaseServerClient } from "./supabase-server";

export async function portalServerJson<T>(path: string): Promise<T | null> {
  const supabase = await getSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) return null;
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) return null;
  return (await response.json()) as T;
}
