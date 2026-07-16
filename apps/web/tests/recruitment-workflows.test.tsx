import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

describe("public recruitment postings", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("renders only API-published summaries with semantic application links", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          {
            slug: "synthetic-advisor-opportunity",
            title: "Synthetic advisor opportunity",
            summary: "A synthetic published fixture.",
            published_at: "2026-07-15T12:00:00Z",
          },
        ],
        total: 1,
        limit: 25,
        offset: 0,
      }),
    });
    vi.stubGlobal("fetch", fetcher);
    const { default: CareersPage } = await import(
      "@/app/(public)/careers/page"
    );
    render(<>{await CareersPage()}</>);
    expect(
      screen.getByRole("heading", { name: "Synthetic advisor opportunity" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: /view synthetic advisor opportunity/i }),
    ).toHaveAttribute("href", "/careers/synthetic-advisor-opportunity");
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/recruitment/postings?limit=25&offset=0"),
      expect.objectContaining({ next: { revalidate: 10 } }),
    );
  });

  it("shows an honest unavailable state when the public API fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const { default: CareersPage } = await import(
      "@/app/(public)/careers/page"
    );
    render(<>{await CareersPage()}</>);
    expect(screen.getByRole("alert")).toHaveTextContent(
      /opportunities are temporarily unavailable/i,
    );
  });
});
