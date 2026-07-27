import { candidateBrowserRequest } from "./candidate-browser-api";

// Both portals use the same signed Supabase session transport. The API remains
// authoritative for role, active-state, and AAL2 administration checks.
export const adminBrowserRequest = candidateBrowserRequest;
