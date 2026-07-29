import type { components } from "@keeper/contracts";
import { portalServerJson } from "./portal-server-api";

type LeadListResponse = components["schemas"]["LeadListResponse"];
type CandidateQueueResponse = components["schemas"]["CandidateQueueResponse"];
type BorrowerReviewQueueResponse =
  components["schemas"]["BorrowerReviewQueueResponse"];

export type AdminOverviewItem = {
  id: string;
  title: string;
  status: string;
  href: string;
  detail: string;
};

export type AdminOverviewSection = {
  total: number;
  items: AdminOverviewItem[];
};

export type AdminOverview = {
  leads: AdminOverviewSection;
  candidates: AdminOverviewSection;
  borrowers: AdminOverviewSection;
};

const EMPTY_SECTION: AdminOverviewSection = { total: 0, items: [] };

function shortId(id: string) {
  return id.slice(0, 8);
}

export async function getAdminOverview(): Promise<AdminOverview> {
  const [leads, candidates, borrowers] = await Promise.all([
    portalServerJson<LeadListResponse>("/api/v1/leads?limit=5&offset=0"),
    portalServerJson<CandidateQueueResponse>(
      "/api/v1/admin/candidates?limit=5&offset=0",
    ),
    portalServerJson<BorrowerReviewQueueResponse>(
      "/api/v1/borrower-applications/review-queue?limit=5&offset=0",
    ),
  ]);

  return {
    leads: leads
      ? {
          total: leads.total,
          items: leads.items.slice(0, 5).map((lead) => ({
            id: lead.id,
            title: lead.name || `Lead ${shortId(lead.id)}`,
            status: lead.status,
            href: `/admin/leads?status=${lead.status}`,
            detail: `${lead.preferred_contact_method} contact · ${lead.mortgage_objective}`,
          })),
        }
      : EMPTY_SECTION,
    candidates: candidates
      ? {
          total: candidates.total,
          items: candidates.items.slice(0, 5).map((candidate) => {
            const fullName = [candidate.given_name, candidate.family_name]
              .filter(Boolean)
              .join(" ")
              .trim();
            return {
              id: candidate.application_id,
              title:
                fullName || `Candidate ${shortId(candidate.application_id)}`,
              status: candidate.status,
              href: "/admin/candidates",
              detail: candidate.source_posting_title,
            };
          }),
        }
      : EMPTY_SECTION,
    borrowers: borrowers
      ? {
          total: borrowers.total,
          items: borrowers.items.slice(0, 5).map((application) => ({
            id: application.application_id,
            title: `Borrower application ${shortId(application.application_id)}`,
            status: application.lifecycle_status,
            href: "/admin/borrower-applications",
            detail: application.assigned_agent_name
              ? `Assigned to ${application.assigned_agent_name}`
              : "Awaiting assignment",
          })),
        }
      : EMPTY_SECTION,
  };
}
