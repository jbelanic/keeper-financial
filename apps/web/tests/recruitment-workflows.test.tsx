import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

describe("public recruitment postings", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("features the single published opportunity without bypassing role review", async () => {
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
    const { container } = render(<>{await CareersPage()}</>);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Build your mortgage business. Keep more control.",
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(
      screen.getByRole("img", {
        name: /editorial image of three professionals in conversation/i,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Synthetic advisor opportunity" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("A synthetic published fixture."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "What you can build with Keeper" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "What the candidate journey looks like",
      }),
    ).toBeInTheDocument();

    const detailLinks = screen.getAllByRole("link", {
      name: "Explore the current opportunity",
    });
    expect(detailLinks).toHaveLength(3);
    expect(
      detailLinks.every(
        (link) =>
          link.getAttribute("href") ===
          "/careers/synthetic-advisor-opportunity",
      ),
    ).toBe(true);
    expect(container.querySelector('a[href^="/auth/register"]')).toBeNull();
    expect(
      screen.getByText(/review the role before creating an account/i),
    ).toBeInTheDocument();
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/recruitment/postings?limit=25&offset=0"),
      expect.objectContaining({ next: { revalidate: 10 } }),
    );
  });

  it("keeps the recruitment story but removes opportunity CTAs when none are published", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ items: [], total: 0, limit: 25, offset: 0 }),
      }),
    );
    const { default: CareersPage } = await import(
      "@/app/(public)/careers/page"
    );
    const { container } = render(<>{await CareersPage()}</>);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Build your mortgage business. Keep more control.",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "No opportunities are currently published",
      }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Explore the current opportunity" }),
    ).not.toBeInTheDocument();
    expect(container.querySelector('a[href^="/auth/register"]')).toBeNull();
  });

  it("shows an honest unavailable state without exposing a posting when the public API fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const { default: CareersPage } = await import(
      "@/app/(public)/careers/page"
    );
    const { container } = render(<>{await CareersPage()}</>);

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Build your mortgage business. Keep more control.",
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      /opportunities are temporarily unavailable/i,
    );
    expect(
      screen.queryByRole("link", { name: "Explore the current opportunity" }),
    ).not.toBeInTheDocument();
    expect(container.querySelector('a[href^="/auth/register"]')).toBeNull();
  });

  it("renders every posting when the API unexpectedly returns more than one", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          items: [
            {
              slug: "first-opportunity",
              title: "First opportunity",
              summary: "First published summary.",
            },
            {
              slug: "second-opportunity",
              title:
                "Second opportunity with an intentionally long dynamic title that must remain readable",
              summary: "Second published summary.",
            },
          ],
          total: 2,
          limit: 25,
          offset: 0,
        }),
      }),
    );
    const { default: CareersPage } = await import(
      "@/app/(public)/careers/page"
    );
    const { container } = render(<>{await CareersPage()}</>);

    expect(
      screen.getByRole("heading", { name: "First opportunity" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "Second opportunity with an intentionally long dynamic title that must remain readable",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "View First opportunity" }),
    ).toHaveAttribute("href", "/careers/first-opportunity");
    expect(
      screen.getByRole("link", {
        name: "View Second opportunity with an intentionally long dynamic title that must remain readable",
      }),
    ).toHaveAttribute("href", "/careers/second-opportunity");
    expect(container.querySelector('a[href^="/auth/register"]')).toBeNull();
  });

  it("keeps plain-text posting content, warnings and both posting-bound account paths", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          slug: "synthetic-advisor-opportunity",
          title: "Synthetic <strong>advisor</strong> opportunity",
          summary: '<img src="x" onerror="alert(1)"> Published summary.',
          body: '<script>alert("unsafe")</script> Test-only posting body.',
        }),
      }),
    );
    const { default: PostingPage } = await import(
      "@/app/(public)/careers/[slug]/page"
    );
    const { container } = render(
      <>
        {await PostingPage({
          params: Promise.resolve({ slug: "synthetic-advisor-opportunity" }),
        })}
      </>,
    );

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Synthetic <strong>advisor</strong> opportunity",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText('<img src="x" onerror="alert(1)"> Published summary.'),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        '<script>alert("unsafe")</script> Test-only posting body.',
      ),
    ).toBeInTheDocument();
    expect(container.querySelector("strong, img, script")).toBeNull();
    expect(
      screen.getByRole("heading", { name: "How the application works" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Before you apply" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/does not guarantee an interview/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/do not include government identification/i),
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", { name: "Create an account" }),
    ).toHaveAttribute(
      "href",
      "/auth/register?posting=synthetic-advisor-opportunity",
    );
    expect(
      screen.getByRole("link", { name: "Sign in with an existing account" }),
    ).toHaveAttribute(
      "href",
      "/auth/sign-in?posting=synthetic-advisor-opportunity",
    );
  });
});
