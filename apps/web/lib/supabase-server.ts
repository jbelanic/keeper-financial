import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { KEEPER_AUTH_COOKIE } from "./supabase-keys";

export const supabaseServerUrl = () =>
  process.env.SUPABASE_INTERNAL_URL ??
  process.env.NEXT_PUBLIC_SUPABASE_URL ??
  "http://127.0.0.1:54321";

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
