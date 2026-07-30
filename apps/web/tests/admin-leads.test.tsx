import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import Loading from "@/app/(admin)/admin/leads/loading";
import { LeadQueue, LeadQueueError } from "@/app/(admin)/admin/leads/page";
import { WithdrawalControl } from "@/app/(admin)/admin/leads/withdrawal-control";
import {
  adminLeadListRequest,
  adminMarketingWithdrawalRequest,
  adminLeadStatusRequest,
  parseLeadQueueSearchParams,
  type AdminLeadList,
} from "@/lib/admin-leads";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const data: AdminLeadList = {
  total: 26,
  limit: 25,
  offset: 0,
  items: [
    {
      id: "00000000-0000-4000-8000-000000000001",
      name: "Synthetic Lead",
      email: "lead@example.com",
      telephone: "+1 416 555 0100",
      mortgage_objective: "renewal",
      preferred_contact_method: "email",
      preferred_agent_slug: "published-agent",
      message: "Please contact me next week.",
      source: "website_apply",
      status: "new",
      created_at: "2026-07-14T12:00:00Z",
      service_consent: {
        state: "granted",
        granted_at: "2026-07-14T12:00:00Z",
        withdrawn_at: null,
      },
      marketing_consent: {
        state: "granted",
        granted_at: "2026-07-14T12:00:00Z",
        withdrawn_at: null,
      },
    },
  ],
};

describe("admin lead queue", () => {
  it("fetches through authenticated FastAPI with no-store and safe filters only", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => data,
    });
    const fetcher = fetchMock as unknown as typeof fetch;

    await expect(
      adminLeadListRequest(
        "synthetic-token",
        { page: 2, status: "new" },
        fetcher,
      ),
    ).resolves.toEqual(data);
    expect(fetcher).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/leads?limit=25&offset=25&status=new",
      {
        headers: { Authorization: "Bearer synthetic-token" },
        cache: "no-store",
      },
    );
    expect(JSON.stringify(fetchMock.mock.calls)).not.toMatch(
      /email|message|private/i,
    );
  });

  it("accepts only bounded page and lifecycle status URL filters", () => {
    expect(
      parseLeadQueueSearchParams({ page: "2", status: "contacted" }),
    ).toEqual({
      page: 2,
      status: "contacted",
    });
    expect(
      parseLeadQueueSearchParams({
        page: "-1",
        status: "pending",
        email: "private@example.com",
      }),
    ).toEqual({ page: 1, status: undefined });
  });

  it("withdraws through the authenticated no-store API boundary without a payload", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => data.items[0].marketing_consent,
    });
    const fetcher = fetchMock as unknown as typeof fetch;
    await adminMarketingWithdrawalRequest(
      "synthetic-token",
      "00000000-0000-4000-8000-000000000001",
      fetcher,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/leads/00000000-0000-4000-8000-000000000001/marketing-consent/withdrawal",
      {
        method: "POST",
        headers: { Authorization: "Bearer synthetic-token" },
        cache: "no-store",
      },
    );
    expect(fetchMock.mock.calls[0][1]).not.toHaveProperty("body");
  });

  it("updates lead status through the authenticated no-store API boundary", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        id: "00000000-0000-4000-8000-000000000001",
        status: "contacted",
      }),
    });
    const fetcher = fetchMock as unknown as typeof fetch;
    await adminLeadStatusRequest(
      "synthetic-token",
      "00000000-0000-4000-8000-000000000001",
      "contacted",
      fetcher,
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/leads/00000000-0000-4000-8000-000000000001/status",
      {
        method: "POST",
        headers: {
          Authorization: "Bearer synthetic-token",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: "contacted" }),
        cache: "no-store",
      },
    );
  });

  it("renders necessary lead details, text consent states, and bounded pagination", () => {
    render(
      <LeadQueue
        data={data}
        page={1}
        status="new"
        withdrawAction={vi.fn()}
        statusAction={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("heading", { name: "Synthetic Lead" }),
    ).toBeInTheDocument();
    expect(screen.getByText("lead@example.com")).toBeInTheDocument();
    expect(
      screen.getByText(/Service acknowledgement: Granted/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Marketing consent: Granted/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Next page" })).toHaveAttribute(
      "href",
      "/admin/leads?page=2&status=new",
    );
    expect(
      screen.queryByRole("link", { name: "Previous page" }),
    ).not.toBeInTheDocument();
    expect(screen.getByLabelText("Set status for Synthetic Lead")).toHaveValue(
      "new",
    );
    expect(
      screen.getByRole("button", { name: "Update status for Synthetic Lead" }),
    ).toBeInTheDocument();
  });

  it("renders a useful empty state", () => {
    render(
      <LeadQueue
        data={{ ...data, total: 0, items: [] }}
        page={1}
        withdrawAction={vi.fn()}
      />,
    );
    expect(
      screen.getByRole("heading", { name: /No leads found/i }),
    ).toBeInTheDocument();
  });

  it("renders useful loading and safe error states", () => {
    const { rerender } = render(<Loading />);
    expect(screen.getByRole("status")).toHaveTextContent(
      /Loading the lead queue/i,
    );
    rerender(<LeadQueueError />);
    expect(screen.getByRole("alert")).toHaveTextContent(/could not be loaded/i);
    expect(screen.getByRole("alert")).not.toHaveTextContent(
      /token|payload|query/i,
    );
  });

  it("requires an explicit accessible confirmation before withdrawal", async () => {
    const action = vi.fn().mockResolvedValue(undefined);
    render(
      <WithdrawalControl
        leadId="00000000-0000-4000-8000-000000000001"
        action={action}
      />,
    );

    const trigger = screen.getByRole("button", {
      name: /Withdraw marketing consent/i,
    });
    trigger.focus();
    fireEvent.click(trigger);
    const dialog = screen.getByRole("dialog");
    expect(dialog).toHaveAttribute("open");
    expect(dialog).toHaveTextContent(
      /does not affect the required service acknowledgement/i,
    );
    const cancel = screen.getByRole("button", { name: "Cancel" });
    const confirm = screen.getByRole("button", { name: "Confirm" });
    expect(cancel).toHaveFocus();
    fireEvent.keyDown(cancel, { key: "Tab", shiftKey: true });
    expect(confirm).toHaveFocus();
    fireEvent.keyDown(confirm, { key: "Tab" });
    expect(cancel).toHaveFocus();
    fireEvent.keyDown(cancel, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    await waitFor(() => expect(trigger).toHaveFocus());
    expect(action).not.toHaveBeenCalled();

    fireEvent.click(
      screen.getByRole("button", { name: /Withdraw marketing consent/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    await waitFor(() => expect(action).toHaveBeenCalledTimes(1));
    const formData = action.mock.calls[0][0] as FormData;
    expect(formData.get("lead_id")).toBe(
      "00000000-0000-4000-8000-000000000001",
    );
    expect(refresh).toHaveBeenCalled();
  });

  it("keeps pending withdrawal modal and announces action errors inside it", async () => {
    let rejectAction!: (reason: Error) => void;
    const action = vi.fn().mockReturnValue(
      new Promise<void>((_resolve, reject) => {
        rejectAction = reject;
      }),
    );
    render(
      <WithdrawalControl
        leadId="00000000-0000-4000-8000-000000000001"
        action={action}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: /Withdraw marketing consent/i }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    rejectAction(new Error("synthetic action failure"));
    const dialog = screen.getByRole("dialog");
    expect(await within(dialog).findByRole("alert")).toHaveTextContent(
      /could not be completed/i,
    );
  });
});
