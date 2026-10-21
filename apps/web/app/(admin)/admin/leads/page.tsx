import type { Metadata } from "next";
import Link from "next/link";
import { EmptyState, ErrorState } from "@keeper/ui";
import {
  fetchAdminLeadList,
  fetchAssignableAgents,
  LEAD_STATUSES,
  parseLeadQueueSearchParams,
  type AdminLeadList,
  type AssignableAgent,
  type LeadStatus,
} from "@/lib/admin-leads";
import {
  assignLeadAgent,
  updateLeadStatus,
  withdrawMarketingConsent,
} from "./actions";
import { WithdrawalControl } from "./withdrawal-control";

export const metadata: Metadata = { title: "Lead queue" };

function timestamp(value: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Toronto",
  }).format(new Date(value));
}

function pageHref(page: number, status?: LeadStatus): string {
  const query = new URLSearchParams({ page: String(page) });
  if (status) query.set("status", status);
  return `/admin/leads?${query.toString()}`;
}

function statusLabel(status: LeadStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function LeadQueue({
  data,
  page,
  status,
  agents = [],
  withdrawAction = withdrawMarketingConsent,
  assignAction = assignLeadAgent,
  statusAction = updateLeadStatus,
}: {
  data: AdminLeadList;
  page: number;
  status?: LeadStatus;
  agents?: AssignableAgent[];
  withdrawAction?: (formData: FormData) => Promise<void>;
  assignAction?: (formData: FormData) => Promise<void>;
  statusAction?: (formData: FormData) => Promise<void>;
}) {
  if (data.items.length === 0) {
    return (
      <EmptyState title="No leads found">
        No leads match this safe status filter.
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
      <div className="lead-queue">
        {data.items.map((lead) => (
          <article className="card lead-card" key={lead.id}>
            <header>
              <p className="eyebrow">{lead.status}</p>
              <h2>{lead.name}</h2>
              <p>Received {timestamp(lead.created_at)}</p>
            </header>
            <dl className="lead-details">
              <div>
                <dt>Email</dt>
                <dd>{lead.email}</dd>
              </div>
              <div>
                <dt>Telephone</dt>
                <dd>{lead.telephone}</dd>
              </div>
              <div>
                <dt>Preferred contact</dt>
                <dd>{lead.preferred_contact_method}</dd>
              </div>
              <div>
                <dt>Objective</dt>
                <dd>{lead.mortgage_objective}</dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{lead.source}</dd>
              </div>
              <div>
                <dt>Assigned agent</dt>
                <dd>{lead.assigned_agent_name ?? "Unassigned"}</dd>
              </div>
              {lead.preferred_agent_slug || lead.preferred_agent_name ? (
                <div>
                  <dt>Legacy agent note</dt>
                  <dd>
                    {lead.preferred_agent_name ?? lead.preferred_agent_slug}
                  </dd>
                </div>
              ) : null}
            </dl>
            <section aria-label="Lead message">
              <h3>Message</h3>
              <p className="break-anywhere">
                {lead.message ?? "No message provided."}
              </p>
            </section>
            <section aria-label="Consent state" className="lead-consents">
              <h3>Consent</h3>
              <p>
                Service acknowledgement: Granted{" "}
                {timestamp(lead.service_consent.granted_at)}
              </p>
              <p>
                Marketing consent:{" "}
                {lead.marketing_consent
                  ? lead.marketing_consent.state === "withdrawn"
                    ? `Withdrawn ${timestamp(lead.marketing_consent.withdrawn_at!)}`
                    : `Granted ${timestamp(lead.marketing_consent.granted_at)}`
                  : "Not granted"}
              </p>
              {lead.marketing_consent?.state === "granted" ? (
                <WithdrawalControl leadId={lead.id} action={withdrawAction} />
              ) : null}
            </section>
            <section aria-label="Lead assignment" className="lead-actions">
              <h3>Assign to an agent</h3>
              <p>
                {lead.assigned_agent_name
                  ? `Owned by ${lead.assigned_agent_name}${
                      lead.assigned_at
                        ? ` since ${timestamp(lead.assigned_at)}`
                        : ""
                    }.`
                  : "Unassigned: this request is in the shared queue."}
              </p>
              <form action={assignAction} className="inline-form">
                <input type="hidden" name="lead_id" value={lead.id} />
                <label htmlFor={`lead-${lead.id}-agent`}>
                  Owning agent for {lead.name}
                </label>
                <select
                  id={`lead-${lead.id}-agent`}
                  name="agent_user_id"
                  defaultValue={lead.assigned_agent_user_id ?? ""}
                >
                  <option value="">Unassigned</option>
                  {agents.map((agent) => (
                    <option key={agent.user_id} value={agent.user_id}>
                      {agent.display_name}
                    </option>
                  ))}
                </select>
                <button className="button" type="submit">
                  Save assignment for {lead.name}
                </button>
              </form>
            </section>
            <section aria-label="Lead status action" className="lead-actions">
              <h3>Lead status</h3>
              <form action={statusAction} className="inline-form">
                <input type="hidden" name="lead_id" value={lead.id} />
                <label htmlFor={`lead-${lead.id}-status`}>
                  Set status for {lead.name}
                </label>
                <select
                  id={`lead-${lead.id}-status`}
                  name="status"
                  defaultValue={lead.status}
                >
                  {LEAD_STATUSES.map((item) => (
                    <option key={item} value={item}>
                      {statusLabel(item)}
                    </option>
                  ))}
                </select>
                <button className="button" type="submit">
                  Update status for {lead.name}
                </button>
              </form>
            </section>
          </article>
        ))}
      </div>
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
        <p>Review bounded contact requests and their explicit consent state.</p>
      </header>
      <form className="queue-filter" method="get">
        <label htmlFor="status">Status</label>
        <select id="status" name="status" defaultValue={params.status ?? ""}>
          <option value="">All statuses</option>
          {LEAD_STATUSES.map((item) => (
            <option key={item} value={item}>
              {item}
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
