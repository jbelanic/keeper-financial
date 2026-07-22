import { createBrowserClient } from "@supabase/ssr";
import { KEEPER_AUTH_COOKIE } from "./supabase-keys";

// Single browser-side Supabase client factory.
//
// MUST use the same cookie name as the server client (KEEPER_AUTH_COOKIE).
// Without it, the browser client derives a different storage key from
// NEXT_PUBLIC_SUPABASE_URL and can never read the session the server set.
export function createKeeperBrowserClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? "http://127.0.0.1:54321",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "local-placeholder",
    { cookieOptions: { name: KEEPER_AUTH_COOKIE } },
  );
}
