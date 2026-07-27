import { candidateBrowserRequest } from "./candidate-browser-api";

// Agents use the same signed Supabase session transport as other portals.
// The API remains authoritative for agent role, active-state, AAL2, and exact
// assigned-application checks.
export const agentBrowserRequest = candidateBrowserRequest;
