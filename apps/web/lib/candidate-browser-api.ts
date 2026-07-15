import { createBrowserClient } from "@supabase/ssr";
import { apiBaseUrl } from "./recruitment-api";

export async function candidateBrowserRequest(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "local-placeholder",
  );
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
  if (!response.ok)
    throw new Error(`candidate request failed (${response.status})`);
  return (await response.json()) as T;
}
