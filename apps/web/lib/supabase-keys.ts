// Shared Supabase auth storage key for the Keeper deployment.
//
// The @supabase/supabase-js client derives its cookie/storage key from the
// URL hostname by default (`sb-<host>-auth-token`). The server-side client
// reaches Supabase via SUPABASE_INTERNAL_URL (the local CLI host gateway for
// dev/test, or the owner-hosted project for production) while the browser
// client uses the browser-facing NEXT_PUBLIC_SUPABASE_URL. Without an
// explicit shared key the two clients write and read DIFFERENT cookie names,
// so the browser never sees the session the server set -> MFA reports
// "assurance level: null" and login fails.
//
// Pinning one explicit name on every client keeps the session cookie coherent
// across server routes and browser components regardless of which URL each
// client connects through.
export const KEEPER_AUTH_COOKIE = "keeper-auth-token";
