import "@testing-library/jest-dom/vitest";

// The web test suite exercises the dev/test local Supabase CLI identity shape
// (decision 46): the browser-facing URL is the loopback CLI endpoint. Production
// code must still fail closed when NEXT_PUBLIC_SUPABASE_URL is unset, which the
// runtime-routing test asserts separately; this default only models the local
// dev/test environment that the rest of the suite targets.
process.env.NEXT_PUBLIC_SUPABASE_URL ??= "http://127.0.0.1:54321";
process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??= "local-placeholder";
