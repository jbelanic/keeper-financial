import { startCandidateApplication } from "@/lib/candidate-provisioning";

describe("candidate application provisioning bridge", () => {
  it("passes only the signed bearer identity and bounded posting path", async () => {
    const fetcher = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: "00000000-0000-4000-8000-000000000111" }),
    }) as unknown as typeof fetch;
    await expect(
      startCandidateApplication(
        "signed-token",
        "synthetic-opportunity",
        fetcher,
      ),
    ).resolves.toEqual({ id: "00000000-0000-4000-8000-000000000111" });
    expect(fetcher).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/v1/recruitment/postings/synthetic-opportunity/applications/start",
      ),
      {
        method: "POST",
        headers: { Authorization: "Bearer signed-token" },
        cache: "no-store",
      },
    );
  });

  it("rejects an unsafe posting before making a request", async () => {
    const fetcher = vi.fn() as unknown as typeof fetch;
    await expect(
      startCandidateApplication("signed-token", "../admin", fetcher),
    ).rejects.toThrow("invalid posting");
    expect(fetcher).not.toHaveBeenCalled();
  });
});
