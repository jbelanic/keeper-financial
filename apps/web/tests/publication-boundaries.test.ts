const notFound = vi.fn(() => {
  throw new Error("NEXT_NOT_FOUND");
});

vi.mock("next/navigation", () => ({ notFound }));

describe("dynamic publication boundaries", () => {
  it("returns non-public behavior for agent slugs until approved publication exists", async () => {
    const { default: AgentProfilePage } = await import(
      "@/app/(public)/agents/[slug]/page"
    );
    expect(() => AgentProfilePage()).toThrow("NEXT_NOT_FOUND");
  });

  it("returns non-public behavior for recruitment slugs until approved postings exist", async () => {
    const { default: CareerOpportunityPage } = await import(
      "@/app/(public)/careers/[slug]/page"
    );
    expect(() => CareerOpportunityPage()).toThrow("NEXT_NOT_FOUND");
  });
});
