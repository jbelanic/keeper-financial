import { createBrowserClient } from "@supabase/ssr";
import { KEEPER_AUTH_COOKIE } from "./supabase-keys";

// Single browser-side Supabase client factory.
//
// MUST use the same cookie name as the server client (KEEPER_AUTH_COOKIE).
// Without it, the browser client derives a different storage key from
// NEXT_PUBLIC_SUPABASE_URL and can never read the session the server set.
export function createKeeperBrowserClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!url) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_URL must be set; refusing to fall back to a loopback Supabase URL.",
    );
  }
  return createBrowserClient(
    url,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "local-placeholder",
    { cookieOptions: { name: KEEPER_AUTH_COOKIE } },
  );
}
