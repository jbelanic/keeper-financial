import { render, screen } from "@testing-library/react";

const notFound = vi.fn(() => {
  throw new Error("NEXT_NOT_FOUND");
});

vi.mock("next/navigation", () => ({ notFound }));

const summary = {
  slug: "synthetic-agent",
  licensed_name: "Synthetic Agent",
  approved_title: "Mortgage Agent Level 2",
  licence_number: "M00000000",
  languages: ["English", "French"],
  service_areas: ["London"],
  specialties: ["Purchases"],
  photo_url: null,
  photo_alt_text: null,
};

describe("published agent profiles", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("fetches the directory server-side without caching and renders safe summaries", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ items: [summary], total: 1, limit: 25, offset: 0 }),
    });
    vi.stubGlobal("fetch", fetcher);
    const { default: AgentsPage } = await import("@/app/(public)/agents/page");
    render(<>{await AgentsPage()}</>);

    expect(
      screen.getByRole("heading", { name: "Synthetic Agent" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /view synthetic agent/i }),
    ).toHaveAttribute("href", "/agents/synthetic-agent");
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/agents?limit=25&offset=0"),
      expect.objectContaining({ cache: "no-store" }),
    );
  });

  it("renders agent and configured brokerage regulatory fields with safe attribution", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          ...summary,
          biography: "A public-safe synthetic biography.",
          public_email: "synthetic.agent@example.test",
          public_phone: "+1 555 010 0200",
          social_links: [
            {
              label: "LinkedIn",
              url: "https://www.linkedin.com/in/synthetic-agent",
            },
          ],
        }),
      }),
    );
    const { default: AgentProfilePage } = await import(
      "@/app/(public)/agents/[slug]/page"
    );
    render(
      <>
        {await AgentProfilePage({
          params: Promise.resolve({ slug: "synthetic-agent" }),
        })}
      </>,
    );

    expect(
      screen.getByRole("heading", { name: "Synthetic Agent" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/Licence M00000000/)).toBeInTheDocument();
    expect(screen.getByText("Keeper Financial Inc.")).toBeInTheDocument();
    expect(screen.getByText("FSCO # 13696")).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: /contact synthetic agent/i,
      }),
    ).toHaveAttribute("href", "/apply?agent=synthetic-agent");
    expect(document.body.textContent).not.toMatch(
      /approved_by|actor_user|internal_notes|audit|transition reason/i,
    );
  });

  it("returns not-found when publication cannot be proved", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );
    const { default: AgentProfilePage } = await import(
      "@/app/(public)/agents/[slug]/page"
    );
    await expect(
      AgentProfilePage({
        params: Promise.resolve({ slug: "draft-agent" }),
      }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
  });
});
