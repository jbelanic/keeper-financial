"use client";

import { useEffect, useState } from "react";
import { Button, Card, ErrorSummary, StatusBadge } from "@keeper/ui";
import { agentBrowserRequest } from "@/lib/agent-browser-api";
import { formatPhoneDisplay, phoneTelHref } from "@/lib/phone";
import type {
  AgentLeadDetail,
  AgentLeadList,
  AgentLeadSummary,
} from "@/lib/agent-api";

type Requester = (path: string, init?: RequestInit) => Promise<Response>;

const OBJECTIVE_LABELS: Record<string, string> = {
  purchase: "Purchase",
  refinance: "Refinance",
  renewal: "Renewal",
  investment: "Investment property",
  other: "Other",
};

function timestamp(value: string): string {
  return new Intl.DateTimeFormat("en-CA", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Toronto",
  }).format(new Date(value));
}

function LeadDetails({ lead }: { lead: AgentLeadDetail }) {
  return (
    <div className="lead-details">
      <dl>
        <div>
          <dt>Email</dt>
          <dd>
            <a href={`mailto:${lead.email}`}>{lead.email}</a>
          </dd>
        </div>
        <div>
          <dt>Telephone</dt>
          <dd>
            <a href={phoneTelHref(lead.telephone)}>
              {formatPhoneDisplay(lead.telephone)}
            </a>
          </dd>
        </div>
        <div>
          <dt>Preferred contact</dt>
          <dd>{lead.preferred_contact_method}</dd>
        </div>
        <div>
          <dt>Objective</dt>
          <dd>
            {OBJECTIVE_LABELS[lead.mortgage_objective] ??
              lead.mortgage_objective}
          </dd>
        </div>
        <div>
          <dt>Received</dt>
          <dd>{timestamp(lead.created_at)}</dd>
        </div>
        <div>
          <dt>Service consent</dt>
          <dd>
            {lead.service_consent.state === "withdrawn"
              ? `Withdrawn ${timestamp(lead.service_consent.withdrawn_at ?? lead.service_consent.granted_at)}`
              : `Granted ${timestamp(lead.service_consent.granted_at)}`}
          </dd>
        </div>
      </dl>
      <section aria-label="Client message">
        <h4>Message</h4>
        <p className="break-anywhere">
          {lead.message ?? "No message provided."}
        </p>
      </section>
    </div>
  );
}

// Leads explicitly assigned to this agent account. The list is a summary; the
// full contact details are fetched per lead so each read is audited server-side.
export function AgentLeads({
  requester = agentBrowserRequest,
}: {
  requester?: Requester;
}) {
  const [leads, setLeads] = useState<AgentLeadSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [state, setState] = useState<"loading" | "ready" | "unavailable">(
    "loading",
  );
  const [expanded, setExpanded] = useState<AgentLeadDetail | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    let active = true;
    requester("/api/v1/agent/leads?limit=50&offset=0")
      .then(async (response) => {
        if (!active) return;
        if (!response.ok) {
          setState("unavailable");
          return;
        }
        const body = (await response.json()) as AgentLeadList;
        setLeads(body.items);
        setTotal(body.total);
        setState("ready");
      })
      .catch(() => {
        if (active) setState("unavailable");
      });
    return () => {
      active = false;
    };
  }, [requester]);

  async function openLead(leadId: string) {
    if (busyId) return;
    setBusyId(leadId);
    setErrors([]);
    try {
      const response = await requester(`/api/v1/agent/leads/${leadId}`);
      if (!response.ok) throw new Error("lead unavailable");
      setExpanded((await response.json()) as AgentLeadDetail);
    } catch {
      setErrors([
        "The contact details for this request could not be loaded. Try again.",
      ]);
    } finally {
      setBusyId(null);
    }
  }

  return (
    <Card aria-labelledby="agent-leads-heading">
      <h2 id="agent-leads-heading">Leads assigned to me</h2>
      <ErrorSummary errors={errors} />
      {state === "unavailable" ? (
        <p className="muted">
          Your assigned leads could not be loaded. Sign out and sign in again;
          if this continues, contact support.
        </p>
      ) : state === "loading" ? (
        <p className="muted">Loading your assigned leads…</p>
      ) : leads.length === 0 ? (
        <p>No client requests are currently assigned to you.</p>
      ) : (
        <>
          <p>
            {total} client {total === 1 ? "request" : "requests"} assigned to
            you.
          </p>
          <ul className="lead-list">
            {leads.map((lead) => (
              <li key={lead.id}>
                <p>
                  <strong>{lead.name}</strong>{" "}
                  <StatusBadge
                    tone={lead.status === "new" ? "warning" : "neutral"}
                  >
                    {lead.status}
                  </StatusBadge>
                </p>
                <p>
                  {OBJECTIVE_LABELS[lead.mortgage_objective] ??
                    lead.mortgage_objective}{" "}
                  · prefers {lead.preferred_contact_method} · received{" "}
                  {timestamp(lead.created_at)}
                </p>
                <Button
                  type="button"
                  disabled={busyId === lead.id}
                  onClick={() => openLead(lead.id)}
                >
                  {busyId === lead.id
                    ? "Loading…"
                    : `View contact details for ${lead.name}`}
                </Button>
                {expanded?.id === lead.id ? (
                  <LeadDetails lead={expanded} />
                ) : null}
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  );
}
