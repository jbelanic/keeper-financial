const notFound = vi.fn(() => {
  throw new Error("NEXT_NOT_FOUND");
});

vi.mock("next/navigation", () => ({ notFound }));

describe("dynamic publication boundaries", () => {
  it("returns non-public behavior for unpublished agent slugs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );
    const { default: AgentProfilePage } = await import(
      "@/app/(public)/agents/[slug]/page"
    );
    await expect(
      AgentProfilePage({
        params: Promise.resolve({ slug: "unpublished-agent" }),
      }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    vi.unstubAllGlobals();
  });

  it("returns non-public behavior for recruitment slugs until approved postings exist", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404 }),
    );
    const { default: CareerOpportunityPage } = await import(
      "@/app/(public)/careers/[slug]/page"
    );
    await expect(
      CareerOpportunityPage({
        params: Promise.resolve({ slug: "unpublished-opportunity" }),
      }),
    ).rejects.toThrow("NEXT_NOT_FOUND");
    vi.unstubAllGlobals();
  });
});
