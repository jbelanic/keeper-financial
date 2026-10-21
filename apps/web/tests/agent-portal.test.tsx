import { render, screen, waitFor } from "@testing-library/react";

const getAgentAssignedBootstrap = vi.fn();

vi.mock("@/lib/borrower-review-api", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@/lib/borrower-review-api")>();
  return { ...actual, getAgentAssignedBootstrap };
});

function jsonResponse(body: unknown, ok = true) {
  return { ok, json: async () => body } as unknown as Response;
}

describe("agent referral link card", () => {
  it("shows the minted link and offers a copy control", async () => {
    const requester = vi.fn().mockResolvedValue(
      jsonResponse({
        apply_url:
          "https://apply.keeperfinancial.ca/mortgage-application?agent=opaque-code",
      }),
    );
    const { AgentLinkCard } = await import(
      "@/app/(agent)/agent/agent-link-card"
    );
    render(<AgentLinkCard requester={requester} />);
    expect(
      await screen.findByText(/mortgage-application\?agent=opaque-code/),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Copy link" }),
    ).toBeInTheDocument();
    expect(requester).toHaveBeenCalledWith("/api/v1/agent-referral-link");
  });

  it("reports an unavailable link instead of silently rendering nothing", async () => {
    const requester = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: "denied" }, false));
    const { AgentLinkCard } = await import(
      "@/app/(agent)/agent/agent-link-card"
    );
    render(<AgentLinkCard requester={requester} />);
    expect(
      await screen.findByText(/application link could not be loaded/i),
    ).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Copy link" })).toBeNull();
  });

  it("treats a transport failure as unavailable", async () => {
    const requester = vi.fn().mockRejectedValue(new Error("offline"));
    const { AgentLinkCard } = await import(
      "@/app/(agent)/agent/agent-link-card"
    );
    render(<AgentLinkCard requester={requester} />);
    expect(
      await screen.findByText(/application link could not be loaded/i),
    ).toBeInTheDocument();
  });
});

describe("agent console page", () => {
  it("keeps the referral link visible when the assigned queue cannot load", async () => {
    getAgentAssignedBootstrap.mockResolvedValue(null);
    vi.resetModules();
    vi.doMock("@/app/(agent)/agent/agent-link-card", () => ({
      AgentLinkCard: () => (
        <section aria-labelledby="stub-agent-link">
          <h2 id="stub-agent-link">Your application link</h2>
        </section>
      ),
    }));
    const { default: AgentApplicationsPage } = await import(
      "@/app/(agent)/agent/page"
    );
    render(await AgentApplicationsPage());
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "Your application link" }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByText(/assigned applications unavailable/i),
    ).toBeInTheDocument();
  });
});
