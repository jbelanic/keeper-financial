import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, ErrorState } from "@keeper/ui";
import {
  DEFAULT_LEAD_STATUS_FILTER,
  fetchAdminLeadList,
  fetchAssignableAgents,
  LEAD_STATUS_FILTERS,
  parseLeadQueueSearchParams,
  type AdminLeadList,
  type AssignableAgent,
  type LeadStatusFilter,
} from "@/lib/admin-leads";
import {
  assignLeadAgent,
  updateLeadStatus,
  withdrawMarketingConsent,
} from "./actions";
import { LeadTable } from "./lead-table";

export const metadata: Metadata = { title: "Lead queue" };

function pageHref(page: number, status: LeadStatusFilter): string {
  const query = new URLSearchParams({ page: String(page) });
  if (status !== "all") query.set("status", status);
  return `/admin/leads?${query.toString()}`;
}

function filterLabel(status: LeadStatusFilter): string {
  if (status === "all") return "All statuses";
  const label = status.charAt(0).toUpperCase() + status.slice(1);
  return status === DEFAULT_LEAD_STATUS_FILTER ? `${label} (default)` : label;
}

export function LeadQueue({
  data,
  page,
  status = DEFAULT_LEAD_STATUS_FILTER,
  agents = [],
  withdrawAction = withdrawMarketingConsent,
  assignAction = assignLeadAgent,
  statusAction = updateLeadStatus,
}: {
  data: AdminLeadList;
  page: number;
  status?: LeadStatusFilter;
  agents?: AssignableAgent[];
  withdrawAction?: (formData: FormData) => Promise<void>;
  assignAction?: (formData: FormData) => Promise<void>;
  statusAction?: (formData: FormData) => Promise<void>;
}) {
  if (data.items.length === 0) {
    return (
      <EmptyState title="No leads found">
        No leads match this status filter. Choose another status to review
        assigned, contacted, or closed requests.
      </EmptyState>
    );
  }
  const pageCount = Math.max(1, Math.ceil(data.total / data.limit));
  return (
    <>
      <p>
        Showing {data.offset + 1}–
        {Math.min(data.offset + data.items.length, data.total)} of {data.total}{" "}
        leads.
      </p>
      <LeadTable
        data={data}
        agents={agents}
        withdrawAction={withdrawAction}
        assignAction={assignAction}
        statusAction={statusAction}
      />
      <nav className="queue-pagination" aria-label="Lead queue pages">
        {page > 1 ? (
          <Link href={pageHref(page - 1, status)}>Previous page</Link>
        ) : (
          <span />
        )}
        <span>
          Page {page} of {pageCount}
        </span>
        {page < pageCount ? (
          <Link href={pageHref(page + 1, status)}>Next page</Link>
        ) : (
          <span />
        )}
      </nav>
    </>
  );
}

export function LeadQueueError() {
  return (
    <ErrorState title="Lead queue unavailable">
      The lead queue could not be loaded. Try again without changing or exposing
      contact details.
    </ErrorState>
  );
}

export default async function AdminLeadsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const params = parseLeadQueueSearchParams(await searchParams);
  let data: AdminLeadList;
  let agents: AssignableAgent[];
  try {
    data = await fetchAdminLeadList(params);
  } catch {
    return <LeadQueueError />;
  }
  try {
    agents = (await fetchAssignableAgents()).items;
  } catch {
    // Assignment stays unavailable rather than blocking the queue view.
    agents = [];
  }
  return (
    <>
      <header className="foundation-header">
        <p className="eyebrow">Brokerage administration</p>
        <h1>Lead queue</h1>
        <p>
          Review bounded contact requests and their explicit consent state. New
          requests are shown by default; assigned and closed requests stay
          available through the status filter.
        </p>
      </header>
      <form className="queue-filter" method="get">
        <label htmlFor="status">Status</label>
        <select id="status" name="status" defaultValue={params.status}>
          {LEAD_STATUS_FILTERS.map((item) => (
            <option key={item} value={item}>
              {filterLabel(item)}
            </option>
          ))}
        </select>
        <button className="button" type="submit">
          Filter
        </button>
      </form>
      <LeadQueue data={data} agents={agents} {...params} />
    </>
  );
}
