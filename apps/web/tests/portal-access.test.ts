import { portalAccessRequest } from "@/lib/portal-access";

describe("portal API authorization", () => {
  it("returns the caller's own roles on success and forwards identity to the API", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        allowed: true,
        area: "candidate",
        roles: ["candidate", "agent"],
      }),
    }) as unknown as typeof fetch;
    await expect(
      portalAccessRequest("synthetic-token", "candidate", fetcher),
    ).resolves.toEqual({ roles: ["candidate", "agent"] });
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/auth/access?area=candidate"),
      expect.objectContaining({
        headers: { Authorization: "Bearer synthetic-token" },
        cache: "no-store",
        signal: expect.any(AbortSignal),
      }),
    );
    expect(fetcher).toHaveBeenCalledOnce();
  });

  it("denies portal entry when the API denies authorization", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue({ ok: false }) as unknown as typeof fetch;
    await expect(
      portalAccessRequest("synthetic-token", "admin", fetcher),
    ).resolves.toBeNull();
  });

  it("fails closed when the authorization call itself fails", async () => {
    const fetcher = vi
      .fn()
      .mockRejectedValue(new Error("network down")) as unknown as typeof fetch;
    await expect(
      portalAccessRequest("synthetic-token", "agent", fetcher),
    ).resolves.toBeNull();
  });

  it("treats a malformed success body as no known roles", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ roles: "agent" }),
    }) as unknown as typeof fetch;
    await expect(
      portalAccessRequest("synthetic-token", "candidate", fetcher),
    ).resolves.toEqual({ roles: [] });
  });
});
