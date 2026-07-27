import { fireEvent, render, screen } from "@testing-library/react";

const queue = {
  total: 1,
  items: [
    {
      application_id: "00000000-0000-4000-8000-000000000401",
      lifecycle_status: "under_review",
      submitted_at: "2026-07-26T12:00:00Z",
      assigned_agent_id: "00000000-0000-4000-8000-000000000501",
      assigned_agent_name: null,
      assigned_agent_email: null,
    },
  ],
};

const detail = {
  application_id: queue.items[0].application_id,
  lifecycle_status: "under_review",
  revision: 1,
  has_sin: true,
  has_co_borrower: false,
  primary_borrower: {
    first_name: "Jane",
    last_name: "Smith",
    email: "jane@example.test",
    phone: "14165550123",
    date_of_birth: "1988-01-01",
    sin: "046454286",
    marital_status: "married",
    number_of_dependants: 1,
    current_address: { street: "1 King St" },
    employment: [],
    has_sin: true,
  },
  co_borrower: null,
  mortgage_request: { mortgage_objective: "purchase" },
  subject_property: { city: "Toronto" },
  other_properties: [],
  assets: [{ asset_type: "chequing", value: "25000.00" }],
  liabilities: [{ liability_type: "credit_card", current_balance: "4000.00" }],
  additional_notes: "Synthetic full-data note",
  last_activity_at: "2026-07-26T11:00:00Z",
  submitted_at: "2026-07-26T12:00:00Z",
};

const documents = {
  total: 1,
  items: [
    {
      document_id: "00000000-0000-4000-8000-000000000601",
      filename: "notice.pdf",
      mime_type: "application/pdf",
      size_bytes: 1024,
      scan_status: "clean",
      uploaded_at: "2026-07-26T11:30:00Z",
    },
  ],
};

describe("agent borrower review console", () => {
  it("loads the full assigned application with unmasked SIN and financials", async () => {
    const requester = vi.fn(async (path: string) => {
      if (path.endsWith("/agent")) {
        return { ok: true, json: async () => detail } as Response;
      }
      if (path.endsWith("/documents")) {
        return { ok: true, json: async () => documents } as Response;
      }
      return { ok: false, status: 404, json: async () => ({}) } as Response;
    });

    const { AgentAssignedConsole } = await import(
      "@/app/(agent)/agent/agent-console"
    );
    render(<AgentAssignedConsole initialQueue={queue} requester={requester} />);

    fireEvent.click(screen.getByRole("button", { name: "Open" }));
    await screen.findByText("jane@example.test");

    // Agent view surfaces the unmasked SIN (scope B privacy approval)
    expect(screen.getByText("046454286")).toBeInTheDocument();
    // Full financial detail for Filogix population
    expect(
      await screen.findByText(/Synthetic full-data note/),
    ).toBeInTheDocument();
    expect(
      requester.mock.calls.some(([path]) => String(path).endsWith("/agent")),
    ).toBe(true);
  });
});
