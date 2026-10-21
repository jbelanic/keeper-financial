"use client";

import { Fragment, useState } from "react";
import type { components } from "@keeper/contracts";
import { Button, StatusBadge } from "@keeper/ui";
import { LEAD_STATUSES, type LeadStatus } from "@/lib/lead-statuses";
import { WithdrawalControl } from "./withdrawal-control";

type LeadAction = (formData: FormData) => Promise<void>;
type AdminLeadList = components["schemas"]["LeadListResponse"];
type AssignableAgent = components["schemas"]["LeadAssignableAgent"];

function timestamp(value: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Toronto",
  }).format(new Date(value));
}

function statusLabel(status: LeadStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Candidate-provisioned accounts start with the placeholder name "Candidate",
 * so the email is the only reliable way to tell agents apart in this selector.
 */
function agentLabel(agent: AssignableAgent): string {
  const name = agent.display_name.trim();
  if (!name || name.toLowerCase() === agent.email.toLowerCase())
    return agent.email;
  return `${name} — ${agent.email}`;
}

export function LeadTable({
  data,
  agents = [],
  withdrawAction,
  assignAction,
  statusAction,
}: {
  data: AdminLeadList;
  agents?: AssignableAgent[];
  withdrawAction: LeadAction;
  assignAction: LeadAction;
  statusAction: LeadAction;
}) {
  const [openLeadId, setOpenLeadId] = useState<string | null>(null);

  return (
    <div
      className="table-scroll lead-table"
      tabIndex={0}
      role="region"
      aria-label="Lead queue"
    >
      <table>
        <caption className="visually-hidden">Lead queue</caption>
        <thead>
          <tr>
            <th scope="col">Received</th>
            <th scope="col">Name</th>
            <th scope="col">Contact</th>
            <th scope="col">Objective</th>
            <th scope="col">Status</th>
            <th scope="col">Assigned agent</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((lead) => {
            const open = openLeadId === lead.id;
            const detailId = `lead-${lead.id}-detail`;
            return (
              <Fragment key={lead.id}>
                <tr className="lead-summary">
                  <td>{timestamp(lead.created_at)}</td>
                  <td>
                    <strong>{lead.name}</strong>
                  </td>
                  <td className="break-anywhere">
                    <span>{lead.email}</span>
                    <br />
                    <span>{lead.telephone}</span>
                  </td>
                  <td>{lead.mortgage_objective}</td>
                  <td>
                    <StatusBadge
                      tone={lead.status === "new" ? "warning" : "neutral"}
                    >
                      {statusLabel(lead.status)}
                    </StatusBadge>
                  </td>
                  <td>{lead.assigned_agent_name ?? "Unassigned"}</td>
                  <td>
                    <Button
                      type="button"
                      className="lead-toggle"
                      aria-expanded={open}
                      aria-controls={detailId}
                      onClick={() => setOpenLeadId(open ? null : lead.id)}
                    >
                      {open ? "Hide details" : "View details"}
                      <span className="visually-hidden"> for {lead.name}</span>
                    </Button>
                  </td>
                </tr>
                {open ? (
                  <tr id={detailId}>
                    <td className="lead-detail-cell" colSpan={7}>
                      <div className="lead-detail-panel">
                        <dl className="lead-details">
                          <div>
                            <dt>Preferred contact</dt>
                            <dd>{lead.preferred_contact_method}</dd>
                          </div>
                          <div>
                            <dt>Source</dt>
                            <dd>{lead.source}</dd>
                          </div>
                          <div>
                            <dt>Assigned agent</dt>
                            <dd>{lead.assigned_agent_name ?? "Unassigned"}</dd>
                          </div>
                          {lead.preferred_agent_slug ||
                          lead.preferred_agent_name ? (
                            <div>
                              <dt>Legacy agent note</dt>
                              <dd>
                                {lead.preferred_agent_name ??
                                  lead.preferred_agent_slug}
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
                        <section
                          aria-label="Consent state"
                          className="lead-consents"
                        >
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
                            <WithdrawalControl
                              leadId={lead.id}
                              action={withdrawAction}
                            />
                          ) : null}
                        </section>
                        <section
                          aria-label="Lead assignment"
                          className="lead-actions"
                        >
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
                            <input
                              type="hidden"
                              name="lead_id"
                              value={lead.id}
                            />
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
                                <option
                                  key={agent.user_id}
                                  value={agent.user_id}
                                >
                                  {agentLabel(agent)}
                                </option>
                              ))}
                            </select>
                            <button className="button" type="submit">
                              Save assignment for {lead.name}
                            </button>
                          </form>
                        </section>
                        <section
                          aria-label="Lead status action"
                          className="lead-actions"
                        >
                          <h3>Lead status</h3>
                          <form action={statusAction} className="inline-form">
                            <input
                              type="hidden"
                              name="lead_id"
                              value={lead.id}
                            />
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
                      </div>
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
