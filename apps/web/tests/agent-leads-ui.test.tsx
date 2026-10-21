import { fireEvent, render, screen } from "@testing-library/react";

const LEAD_ID = "00000000-0000-4000-8000-0000000000c1";
const RECEIVED = "2026-07-15T12:00:00Z";

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as unknown as Response;
}

const listBody = {
  items: [
    {
      id: LEAD_ID,
      name: "Synthetic Client",
      mortgage_objective: "purchase",
      preferred_contact_method: "telephone",
      status: "new",
      assigned_at: RECEIVED,
      created_at: RECEIVED,
    },
  ],
  total: 1,
  limit: 50,
  offset: 0,
};

const detailBody = {
  id: LEAD_ID,
  name: "Synthetic Client",
  email: "client@example.test",
  telephone: "+1 416 555 0100",
  mortgage_objective: "purchase",
  preferred_contact_method: "telephone",
  message: "Please call me about a first purchase.",
  status: "new",
  assigned_at: RECEIVED,
  created_at: RECEIVED,
  service_consent: {
    state: "granted",
    granted_at: RECEIVED,
    withdrawn_at: null,
  },
  marketing_consent: null,
};

describe("agent assigned leads", () => {
  it("lists assigned leads and loads the full contact details on request", async () => {
    const requester = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(listBody))
      .mockResolvedValueOnce(jsonResponse(detailBody));
    const { AgentLeads } = await import("@/app/(agent)/agent/agent-leads");

    render(<AgentLeads requester={requester} />);

    expect(
      await screen.findByRole("button", {
        name: "View contact details for Synthetic Client",
      }),
    ).toBeInTheDocument();
    // The list itself must not carry contact details.
    expect(screen.queryByText("client@example.test")).toBeNull();

    fireEvent.click(
      screen.getByRole("button", {
        name: "View contact details for Synthetic Client",
      }),
    );

    expect(await screen.findByText("client@example.test")).toBeInTheDocument();
    expect(screen.getByText("+1 416 555 0100")).toBeInTheDocument();
    expect(
      screen.getByText(/please call me about a first purchase/i),
    ).toBeInTheDocument();
    expect(requester).toHaveBeenNthCalledWith(
      1,
      "/api/v1/agent/leads?limit=50&offset=0",
    );
    expect(requester).toHaveBeenNthCalledWith(
      2,
      `/api/v1/agent/leads/${LEAD_ID}`,
    );
  });

  it("reports an unavailable list instead of rendering nothing", async () => {
    const requester = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: "denied" }, false));
    const { AgentLeads } = await import("@/app/(agent)/agent/agent-leads");

    render(<AgentLeads requester={requester} />);

    expect(
      await screen.findByText(/assigned leads could not be loaded/i),
    ).toBeInTheDocument();
  });

  it("keeps the list intact when one detail read fails", async () => {
    const requester = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(listBody))
      .mockResolvedValueOnce(jsonResponse({ detail: "unavailable" }, false));
    const { AgentLeads } = await import("@/app/(agent)/agent/agent-leads");

    render(<AgentLeads requester={requester} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "View contact details for Synthetic Client",
      }),
    );

    expect(
      await screen.findByText(
        /contact details for this request could not be loaded/i,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: "View contact details for Synthetic Client",
      }),
    ).toBeInTheDocument();
  });

  it("reports an empty assignment list plainly", async () => {
    const requester = vi
      .fn()
      .mockResolvedValue(jsonResponse({ ...listBody, items: [], total: 0 }));
    const { AgentLeads } = await import("@/app/(agent)/agent/agent-leads");

    render(<AgentLeads requester={requester} />);

    expect(
      await screen.findByText(
        /no client requests are currently assigned to you/i,
      ),
    ).toBeInTheDocument();
  });
});
