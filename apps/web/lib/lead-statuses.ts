/**
 * Lead lifecycle vocabulary shared by server pages, server actions, and the
 * client-side queue table. Kept free of imports so a client component can use it
 * without pulling in the server-only API/session modules.
 */
export const LEAD_STATUSES = [
  "new",
  "assigned",
  "contacted",
  "closed",
] as const;
export type LeadStatus = (typeof LEAD_STATUSES)[number];

/** The queue defaults to active work: already assigned/closed leads are opt-in. */
export const LEAD_STATUS_FILTERS = [...LEAD_STATUSES, "all"] as const;
export type LeadStatusFilter = (typeof LEAD_STATUS_FILTERS)[number];
export const DEFAULT_LEAD_STATUS_FILTER: LeadStatusFilter = "new";
