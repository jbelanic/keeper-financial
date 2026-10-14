import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { KEEPER_AUTH_COOKIE } from "./supabase-keys";

// Resolve the server-side Supabase origin from configuration only.
//
// There is deliberately no loopback default: production identity is either the
// owner-hosted Supabase project or an explicitly configured local CLI endpoint,
// so a missing URL must fail loudly rather than silently point at 127.0.0.1.
export const supabaseServerUrl = () => {
  const url =
    process.env.SUPABASE_INTERNAL_URL ?? process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!url) {
    throw new Error(
      "Supabase server URL is not configured; set NEXT_PUBLIC_SUPABASE_URL (and optionally SUPABASE_INTERNAL_URL).",
    );
  }
  return url;
};

export async function getSupabaseServerClient() {
  const cookieStore = await cookies();
  return createServerClient(
    supabaseServerUrl(),
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "local-placeholder",
    {
      cookieOptions: { name: KEEPER_AUTH_COOKIE },
      cookies: {
        getAll: () => cookieStore.getAll(),
        setAll: (items) => {
          try {
            items.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options),
            );
          } catch {
            /* Server Components cannot refresh cookies. */
          }
        },
      },
    },
  );
}
