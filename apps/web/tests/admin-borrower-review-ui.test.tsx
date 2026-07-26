import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";

const queue = {
  total: 1,
  items: [
    {
      application_id: "00000000-0000-4000-8000-000000000401",
      lifecycle_status: "submitted",
      submitted_at: "2026-07-26T12:00:00Z",
      assigned_agent_id: null,
      assigned_agent_name: null,
      assigned_agent_email: null,
    },
  ],
};

const eligibleAgents = [
  {
    user_id: "00000000-0000-4000-8000-000000000501",
    email: "agent@example.test",
    display_name: "Synthetic Agent",
  },
];

const detail = {
  application_id: queue.items[0].application_id,
  lifecycle_status: "submitted",
  revision: 1,
  has_sin: true,
  has_co_borrower: false,
  primary_borrower: {
    first_name: "Jane",
    last_name: "Smith",
    email: "jane@example.test",
    phone: "14165550123",
    date_of_birth: "1988-01-01",
    sin: { display: "*** *** 286", last_three: "286" },
    marital_status: "married",
    number_of_dependants: 1,
    current_address: {},
    employment: [],
    has_sin: true,
  },
  co_borrower: null,
  mortgage_request: { mortgage_objective: "purchase" },
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

describe("admin borrower review console", () => {
  it("loads masked review detail, assigns an agent, reveals SIN, and downloads through API", async () => {
    const originalCreateObjectURL = URL.createObjectURL;
    const originalRevokeObjectURL = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn(() => "blob:keeper-borrower-document");
    URL.revokeObjectURL = vi.fn();
    const click = vi.fn();

    const requester = vi.fn(async (path: string, init?: RequestInit) => {
      if (path.endsWith("/internal")) {
        return { ok: true, json: async () => detail } as Response;
      }
      if (path.endsWith("/documents")) {
        return { ok: true, json: async () => documents } as Response;
      }
      if (path.endsWith("/assignment")) {
        expect(JSON.parse(String(init?.body))).toMatchObject({
          agent_user_id: eligibleAgents[0].user_id,
          reason_category: "initial_assignment",
        });
        return {
          ok: true,
          json: async () => ({
            application_id: queue.items[0].application_id,
            lifecycle_status: "under_review",
            assigned_agent_id: eligibleAgents[0].user_id,
            assigned_at: "2026-07-26T12:05:00Z",
          }),
        } as Response;
      }
      if (path.endsWith("/sin/reveal")) {
        return {
          ok: true,
          json: async () => ({
            application_id: queue.items[0].application_id,
            sin: "046454286",
          }),
        } as Response;
      }
      if (path.endsWith("/download")) {
        return {
          ok: true,
          headers: new Headers({
            "content-disposition": 'attachment; filename="notice.pdf"',
          }),
          blob: async () => new Blob(["PDF"]),
        } as Response;
      }
      return { ok: false, status: 404, json: async () => ({}) } as Response;
    });

    const { BorrowerReviewConsole } = await import(
      "@/app/(admin)/admin/borrower-applications/review-console"
    );
    render(
      <BorrowerReviewConsole
        initialQueue={queue}
        eligibleAgents={eligibleAgents}
        requester={requester}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Review" }));
    await screen.findByText("jane@example.test");
    expect(screen.getByText("*** *** 286")).toBeInTheDocument();
    expect(screen.queryByText("046454286")).not.toBeInTheDocument();

    const assignForm = screen.getByRole("heading", { name: /assign agent/i })
      .parentElement as HTMLElement;
    fireEvent.change(
      within(assignForm).getByLabelText(/active mortgage agent/i),
      {
        target: { value: eligibleAgents[0].user_id },
      },
    );
    fireEvent.change(within(assignForm).getByLabelText(/^reason$/i), {
      target: { value: "initial_assignment" },
    });
    fireEvent.click(
      within(assignForm).getByRole("button", { name: /save assignment/i }),
    );
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent(
        /assignment recorded/i,
      ),
    );

    const revealForm = screen.getByRole("heading", { name: /reveal sin/i })
      .parentElement as HTMLElement;
    fireEvent.change(within(revealForm).getByLabelText(/reason/i), {
      target: { value: "credit_review" },
    });
    fireEvent.click(
      within(revealForm).getByRole("button", { name: /reveal sin/i }),
    );
    await screen.findByText(/046454286/);

    vi.spyOn(document, "createElement").mockReturnValue({
      click,
      remove: vi.fn(),
      set href(_value: string) {},
      set download(_value: string) {},
      set rel(_value: string) {},
    } as unknown as HTMLAnchorElement);
    fireEvent.click(screen.getByRole("button", { name: /download/i }));
    await waitFor(() => expect(click).toHaveBeenCalledOnce());
    expect(
      requester.mock.calls.some(([path]) => String(path).endsWith("/download")),
    ).toBe(true);

    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
  });
});
