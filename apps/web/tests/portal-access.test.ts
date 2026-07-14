import { portalAccessRequest } from "@/lib/portal-access";

describe("portal API authorization", () => {
  it("sends identity to the API authorization authority and accepts only success", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue({ ok: true }) as unknown as typeof fetch;
    await expect(
      portalAccessRequest("synthetic-token", "candidate", fetcher),
    ).resolves.toBe(true);
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/access?area=candidate"),
      expect.objectContaining({
        headers: { Authorization: "Bearer synthetic-token" },
        cache: "no-store",
      }),
    );
  });

  it("denies portal entry when the API denies authorization", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue({ ok: false }) as unknown as typeof fetch;
    await expect(
      portalAccessRequest("synthetic-token", "admin", fetcher),
    ).resolves.toBe(false);
  });
});
